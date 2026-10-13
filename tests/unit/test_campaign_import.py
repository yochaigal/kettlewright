import io
import json
import re
import tarfile
import zipfile
from datetime import datetime, timedelta

import pytest

from app.lib.campaign_import import preview_archive, ImportError
from app.models import db, Campaign, ContentEntry, CampaignImport, PointcrawlMap
from test_campaigns import setup, login, create_map, create_entry


def md(title, kind='Note', parent='', body='A **private** description.'):
    return f'---\nlayout: default\ntitle: {title}\ntype: {kind}\n' + (f'parent: {parent}\n' if parent else '') + f'---\n{body}'


def archive(files, kind='zip'):
    stream = io.BytesIO()
    if kind == 'zip':
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as output:
            for name, text in files.items():
                output.writestr(name, text)
    else:
        with tarfile.open(fileobj=stream, mode='w:gz') as output:
            for name, text in files.items():
                data = text.encode()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
    return stream.getvalue()


def upload(client, data):
    return client.post('/materials/import-archive', data={'archive': (io.BytesIO(data), 'campaign.zip')})


@pytest.mark.parametrize('filename', ['article.md', 'drawing.excalidraw', 'campaign.rar'])
def test_unsupported_upload_shows_warning_without_staging(setup, filename):
    app, client = setup
    response = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(b'---\nlayout: default'), filename)})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'role="alert"' in html and 'Unsupported file type' in html
    assert 'archive-confirm-form' not in html
    with app.app_context():
        assert CampaignImport.query.count() == 0
        assert ContentEntry.query.count() == 0


def test_downloadable_example_imports_complete_hierarchy(setup):
    app, client = setup
    response = client.get('/materials/import-example.zip')
    assert response.status_code == 200
    assert response.mimetype == 'application/zip'
    assert 'attachment' in response.headers['Content-Disposition']
    preview = upload(client, response.data)
    html = preview.get_data(as_text=True)
    assert 'Campaigns / My Campaign / My Dungeon' in html
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 302
    with app.app_context():
        room = ContentEntry.query.filter_by(title='The Cellar').one()
        assert room.parent.title == 'My Dungeon'
        assert room.campaign.name == 'My Campaign'
        assert room.parent.pointcrawl.kind == 'dungeon'


@pytest.mark.parametrize('kind',['zip','tar'])
def test_import_into_existing_owned_campaign_keeps_descendants_private(setup,kind):
    app,client=setup
    existing=create_entry(client,title='Existing article')
    # Another owner's identical campaign name must not make ours ambiguous.
    with app.app_context():
        db.session.add(Campaign(owner_id=2,name='Secret campaign'));db.session.commit()
    response=upload(client,archive({'dungeon.md':md('New Dungeon','Dungeon','Secret campaign'),
        'room.md':md('New Room','Dungeon room','New Dungeon')},kind))
    html=response.get_data(as_text=True)
    assert 'Existing campaign:' in html and 'Campaigns / Secret campaign' in html
    token=re.search(r'name="preview_id" value="([a-f0-9]+)"',html).group(1)
    with app.app_context():
        assert ContentEntry.query.count()==1
    assert client.post('/materials/import-archive',data={'preview_id':token}).status_code==302
    with app.app_context():
        assert Campaign.query.filter_by(owner_id=1).count()==1
        dungeon=ContentEntry.query.filter_by(title='New Dungeon').one()
        room=ContentEntry.query.filter_by(title='New Room').one()
        assert dungeon.campaign_id==1 and dungeon.parent_id is None
        assert room.campaign_id==1 and room.parent_id==dungeon.id
        assert dungeon.pointcrawl.kind=='dungeon'
        assert not dungeon.presentations and not room.presentations
        assert db.session.get(ContentEntry,existing).title=='Existing article'
    assert client.post('/materials/import-archive',data={'preview_id':token}).status_code==409


@pytest.mark.parametrize('mode',['duplicate','foreign','missing'])
def test_existing_campaign_lookup_rejects_ambiguous_or_unowned_targets(setup,mode):
    app,client=setup
    name='Secret campaign' if mode=='duplicate' else 'Unavailable campaign'
    with app.app_context():
        if mode!='missing':
            db.session.add(Campaign(owner_id=1 if mode=='duplicate' else 2,name=name));db.session.commit()
    html=upload(client,archive({'dungeon.md':md('Dungeon','Dungeon',name)})).get_data(as_text=True)
    assert 'ambiguous' in html
    assert 'name="preview_id"' not in html
    with app.app_context():
        assert ContentEntry.query.count()==0 and CampaignImport.query.count()==0


@pytest.mark.parametrize('mutation',['rename','delete','transfer','duplicate','replace'])
def test_existing_campaign_is_rechecked_before_atomic_confirmation(setup,mutation):
    app,client=setup
    html=upload(client,archive({'dungeon.md':md('Dungeon','Dungeon','Secret campaign'),
        'new.md':md('New campaign','Campaign')})).get_data(as_text=True)
    token=re.search(r'name="preview_id" value="([a-f0-9]+)"',html).group(1)
    with app.app_context():
        campaign=db.session.get(Campaign,1)
        if mutation in ('rename','replace'): campaign.name='Renamed'
        elif mutation=='delete': db.session.delete(campaign)
        elif mutation=='transfer': campaign.owner_id=2
        if mutation in ('duplicate','replace'): db.session.add(Campaign(owner_id=1,name='Secret campaign'))
        db.session.commit()
        original_count=Campaign.query.count()
    response=client.post('/materials/import-archive',data={'preview_id':token})
    assert response.status_code==409
    with app.app_context():
        assert not db.session.get(CampaignImport,token).consumed
        assert ContentEntry.query.count()==0 and Campaign.query.count()==original_count


def test_archive_parents_take_priority_and_ids_never_resolve_existing_records(setup):
    app,client=setup
    html=upload(client,archive({'campaign.md':md('Secret campaign','Campaign'),
        'dungeon.md':md('Dungeon','Dungeon','Secret campaign')})).get_data(as_text=True)
    assert 'Existing campaign:' not in html
    token=re.search(r'name="preview_id" value="([a-f0-9]+)"',html).group(1)
    assert client.post('/materials/import-archive',data={'preview_id':token}).status_code==302
    with app.app_context():
        assert ContentEntry.query.filter_by(title='Dungeon').one().campaign_id!=1
    data=md('Another dungeon','Dungeon').replace('type: Dungeon\n','type: Dungeon\nparent_id: 1\n')
    html=upload(client,archive({'dungeon.md':data})).get_data(as_text=True)
    assert 'parent_id' in html and 'is missing' in html and 'name="preview_id"' not in html


@pytest.mark.parametrize('same_destination',[True,False])
def test_links_and_references_respect_existing_campaign_destinations(setup,same_destination):
    app,client=setup
    with app.app_context():
        db.session.add(Campaign(owner_id=1,name='Other campaign'));db.session.commit()
    target_parent='Secret campaign' if same_destination else 'Other campaign'
    files={'source.md':md('Source',parent='Secret campaign',body='See [[Target]].')
            .replace('layout: default\n','layout: default\nid: source\n'),
        'target.md':md('Target',parent=target_parent)
            .replace('layout: default\n','layout: default\nid: target\n')}
    with app.app_context():
        preview=preview_archive(archive(files),owner_id=1)
        assert not preview['errors']
        source=next(row for row in preview['rows'] if row['title']=='Source')
        assert bool(source['references'])==same_destination
        files['manifest.json']=json.dumps({'format':'kettlewright-campaign','version':1,
            'links':[{'source':'source','target':'target'}]})
        preview=preview_archive(archive(files),owner_id=1)
        assert bool(preview['errors'])!=same_destination
        if not same_destination:
            assert 'same campaign' in preview['errors'][0]


@pytest.mark.parametrize('kind', ['zip', 'tar'])
def test_preview_confirm_hierarchy_private_and_replay(setup, kind):
    app, client = setup
    data = archive({'room.md': md('Room', 'Location', 'Dungeon'),
        'dungeon.md': md('Dungeon', 'Dungeon', 'My Campaign'),
        'campaign.md': md('My Campaign', 'Campaign'),
        'loose.md': md('Loose'), 'image.png': 'ignored'}, kind)
    response = upload(client, data)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Campaigns / My Campaign / Dungeon' in html and 'Unfiled articles' in html
    assert 'image.png' in html
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    with app.app_context():
        assert ContentEntry.query.count() == 0
        assert Campaign.query.count() == 1
    login(client, 2)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 404
    login(client, 1)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 302
    with app.app_context():
        dungeon = ContentEntry.query.filter_by(title='Dungeon').one()
        room = ContentEntry.query.filter_by(title='Room').one()
        assert room.parent_id == dungeon.id
        assert room.campaign_id == dungeon.campaign_id
        assert dungeon.pointcrawl.kind == 'dungeon'
        assert dungeon.campaign.name == 'My Campaign'
        assert ContentEntry.query.filter_by(title='Loose').one().campaign_id is None
        assert ContentEntry.query.filter_by(category='overview').one().body == 'A **private** description.'
        campaign_id = dungeon.campaign_id
    assert client.get('/party/1/materials/data').json == {'entries': []}
    assert 'Room' in client.get(f'/campaigns/{campaign_id}/').get_data(as_text=True)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 409
    with app.app_context():
        assert Campaign.query.count() == 2


@pytest.mark.parametrize('files,expected', [
    ({'a.md': md('A', parent='Missing')}, 'missing or ambiguous'),
    ({'a.md': md('A', parent='B'), 'b.md': md('B', parent='A')}, 'cycle'),
    ({'a.md': md('A'), 'b.md': md('A'), 'c.md': md('C', parent='A')}, 'ambiguous'),
    ({'a.md': 'No header'}, 'Missing YAML'),
    ({'a.md': md('A', 'Surprise')}, 'Unknown type'),
    ({'a.md': md('A', 'Campaign', 'B')}, 'cannot have a parent'),
    ({'a.md': '---\nlayout: default\ntitle: A\ntitle: B\ntype: Note\n---'}, 'Duplicate'),
    ({'a.md': '---\nlayout: default\ntitle: [A]\ntype: Note\n---'}, 'plain strings'),
    ({'a.md': md('A', body='x' * 50001)}, '50000'),
    ({'a.md': md('A', body='![image](relative.png)')}, 'HTTP(S)'),
])
def test_invalid_preview_never_offers_confirmation(setup, files, expected):
    app, client = setup
    response = upload(client, archive(files))
    html = response.get_data(as_text=True)
    assert expected in html and 'name="preview_id"' not in html
    with app.app_context():
        assert CampaignImport.query.count() == ContentEntry.query.count() == 0


@pytest.mark.parametrize('kind', ['zip', 'tar'])
def test_archive_paths_and_size_are_bounded(kind):
    for filename in ('../escape.md', '/absolute.md', 'C:\\escape.md'):
        with pytest.raises(ImportError, match='Unsafe'):
            preview_archive(archive({filename: md('Bad')}, kind))
    with pytest.raises(ImportError, match='512 KB'):
        preview_archive(archive({'large.md': 'x' * (512 * 1024 + 1)}, kind))
    with pytest.raises(ImportError, match='valid ZIP or TAR'):
        preview_archive(b'not an archive')


def test_preview_expiry_and_csrf(setup):
    app, client = setup
    upload(client, archive({'a.md': md('A')}))
    with app.app_context():
        batch = CampaignImport.query.one()
        token = batch.id
        batch.created_at = datetime.utcnow() - timedelta(hours=2)
        db.session.commit()
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 409
    app.config['WTF_CSRF_ENABLED'] = True
    assert upload(client, archive({'a.md': md('A')})).status_code == 400


def test_import_requires_feature_access(setup):
    app, client = setup
    app.config['FEATURE_TEST_USER_IDS'] = set()
    assert client.get('/materials/import-archive').status_code == 404
    assert upload(client, archive({'a.md': md('A')})).status_code == 404


def test_archive_symlinks_and_member_limit():
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as output:
        member = tarfile.TarInfo('linked.md')
        member.type = tarfile.SYMTYPE
        member.linkname = '/etc/passwd'
        output.addfile(member)
    with pytest.raises(ImportError, match='Links and special'):
        preview_archive(stream.getvalue())
    with pytest.raises(ImportError, match='500 entries'):
        preview_archive(archive({f'{i}.md': md(str(i)) for i in range(501)}))


def test_imported_subtree_moves_and_deletion_preview_includes_children(setup):
    app, client = setup
    response = upload(client, archive({'root.md': md('Root'), 'child.md': md('Child', parent='Root')}))
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', response.get_data(as_text=True)).group(1)
    client.post('/materials/import-archive', data={'preview_id': token})
    with app.app_context():
        root = ContentEntry.query.filter_by(title='Root').one()
        root_id = root.id
    assert client.post(f'/materials/{root_id}/edit', data={'version': 1, 'title': 'Root',
        'body': 'changed', 'category': 'note', 'campaign_id': 1}).status_code == 302
    with app.app_context():
        assert ContentEntry.query.filter_by(title='Child').one().campaign_id == 1
    response = client.post('/materials/bulk-delete', data={'campaign_id': 1, 'entry_ids': root_id, f'version_{root_id}': 2})
    assert response.status_code == 200 and 'Child' in response.get_data(as_text=True)
    token = re.search(r'name="deletion_token" value="([^"]+)"', response.get_data(as_text=True)).group(1)
    assert client.post('/materials/bulk-delete', data={'deletion_token': token}).status_code == 302
    with app.app_context():
        assert ContentEntry.query.count() == 0


def test_subtree_move_preserves_map_workspace_boundaries(setup):
    import json
    app, client = setup
    folder_id = create_entry(client, title='Folder', category='note')
    child_map_id, _ = create_map(client, nodes=0)
    outside_id, graph = create_map(client, nodes=1)
    graph['nodes'][0]['nested_map_id'] = child_map_id
    assert client.post(f'/maps/{outside_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    with app.app_context():
        db.session.add(Campaign(id=2, owner_id=1, name='Destination'))
        db.session.get(PointcrawlMap, child_map_id).entry.parent_id = folder_id
        db.session.commit()
    data = {'version': 1, 'title': 'Folder', 'body': 'Moved', 'category': 'note', 'campaign_id': 2}
    assert client.post(f'/materials/{folder_id}/edit', data=data).status_code == 400
    with app.app_context():
        assert db.session.get(PointcrawlMap, child_map_id).entry.campaign_id == 1
        assert db.session.get(ContentEntry, folder_id).body == 'SECRET BODY'
        db.session.get(PointcrawlMap, outside_id).entry.parent_id = folder_id
        db.session.commit()
    assert client.post(f'/materials/{folder_id}/edit', data=data).status_code == 302
    with app.app_context():
        assert all(entry.campaign_id == 2 for entry in ContentEntry.query.all())
