import io
import json
import re
import tarfile
import zipfile
from datetime import datetime, timedelta

import pytest

from app.lib.campaign_import import preview_archive, single_file_preview, ImportError
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


def confirm(client, token, campaign=1, **extra):
    """Confirm a preview: it becomes a new module of the campaign."""
    return client.post('/materials/import-archive', data={'preview_id': token, 'target_campaign': campaign, **extra})


@pytest.mark.parametrize('filename', ['drawing.excalidraw', 'campaign.rar'])
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


def test_single_md_with_metadata_imports_as_a_module(setup):
    app, client = setup
    content = md('My Note', 'Note')
    response = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(content.encode()), 'my-note.md')})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'My Note' in html and 'Destination: Module' in html and 'Unfiled' not in html
    assert 'archive-confirm-form' in html and 'name="target_campaign" required' in html
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 400  # A campaign is required.
    response = confirm(client, token)
    with app.app_context():
        entry = ContentEntry.query.filter_by(title='My Note').one()
        assert entry.category == 'note' and entry.campaign_id == 1
        assert entry.module.title == 'my-note'  # No front page: named after the file.
        assert response.location.endswith(f'/campaigns/1/modules/{entry.module_id}/')


def test_single_md_without_metadata_infers_defaults_and_imports(setup):
    app, client = setup
    # Plain markdown with no frontmatter — title comes from first heading.
    content = b'# Adventure Log\n\nSome notes from the session.'
    response = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(content), 'adventure-log.md')})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Adventure Log' in html and 'Destination: Module' in html
    assert 'Defaults applied' in html  # warning shown
    assert 'archive-confirm-form' in html
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    assert confirm(client, token).status_code == 302
    with app.app_context():
        entry = ContentEntry.query.filter_by(title='Adventure Log').one()
        assert entry.category == 'note'


def test_single_md_without_metadata_falls_back_to_filename_stem(setup):
    app, client = setup
    content = b'Just some plain text, no heading.'
    response = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(content), 'session-recap.md')})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Session Recap' in html  # title inferred from filename
    assert 'archive-confirm-form' in html


def test_zip_with_missing_metadata_uses_defaults_and_shows_warning(setup):
    app, client = setup
    # Mix: one valid file, one file with no frontmatter.
    files = {
        'campaign.md': md('My Campaign', 'Campaign'),
        'notes.md': '# Field Notes\n\nInteresting observations.',
    }
    response = upload(client, archive(files))
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Field Notes' in html  # inferred from heading
    assert 'Defaults applied' in html  # warning present
    assert 'archive-confirm-form' in html  # no blocking errors


def test_single_file_preview_raises_for_non_meta_errors(setup):
    app, client = setup
    # Frontmatter present but structurally invalid YAML should still be an error.
    content = b'---\nlayout: default\ntitle: {bad: yaml}\ntype: Note\n---\nBody.'
    response = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(content), 'bad.md')})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'archive-confirm-form' not in html


def test_downloadable_example_imports_complete_hierarchy(setup):
    app, client = setup
    response = client.get('/materials/import-example.zip')
    assert response.status_code == 200
    assert response.mimetype == 'application/zip'
    assert 'attachment' in response.headers['Content-Disposition']
    with zipfile.ZipFile(io.BytesIO(response.data)) as example:
        assert {name.split('/')[0] for name in example.namelist()} == {'module.md', 'maps', 'articles', 'backgrounds'}
    preview = upload(client, response.data)
    html = preview.get_data(as_text=True)
    assert 'Module / Alderbridge' in html
    # The preview lists the module's parts apart.
    assert '2 maps · 1 background · 4 articles' in html
    assert html.index('class="import-maps"') < html.index('class="import-preview"') and 'Tidewatcher</strong>' in html
    assert html.count('name="target_campaign"') == 1
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    assert confirm(client, token).status_code == 302
    with app.app_context():
        mara = ContentEntry.query.filter_by(title='Mara the Ferryman').one()
        assert mara.parent.title == 'Alderbridge' and mara.campaign_id == 1 and mara.module.title == 'The Ashen Marches'
        assert ContentEntry.query.filter_by(title='The Sunken Abbey').one().pointcrawl.kind == 'dungeon'


@pytest.mark.parametrize('kind',['zip','tar'])
def test_parent_outside_the_module_is_imported_at_its_top_and_kept_private(setup,kind):
    app,client=setup
    existing=create_entry(client,title='Existing article')
    response=upload(client,archive({'dungeon.md':md('New Dungeon','Dungeon','Secret campaign'),
        'room.md':md('New Room','Dungeon room','New Dungeon')},kind))
    html=response.get_data(as_text=True)
    assert 'is not in this module' in html and 'Existing campaign:' not in html
    token=re.search(r'name="preview_id" value="([a-f0-9]+)"',html).group(1)
    with app.app_context():
        assert ContentEntry.query.count()==1
    assert confirm(client,token).status_code==302
    with app.app_context():
        assert Campaign.query.filter_by(owner_id=1).count()==1
        dungeon=ContentEntry.query.filter_by(title='New Dungeon').one()
        room=ContentEntry.query.filter_by(title='New Room').one()
        assert dungeon.campaign_id==1 and dungeon.parent_id is None
        assert room.campaign_id==1 and room.parent_id==dungeon.id and room.module_id==dungeon.module_id
        assert dungeon.pointcrawl.kind=='dungeon'
        assert not dungeon.presentations and not room.presentations
        assert db.session.get(ContentEntry,existing).title=='Existing article'
    assert confirm(client,token).status_code==409


@pytest.mark.parametrize('mutation',['delete','transfer'])
def test_destination_campaign_is_rechecked_before_atomic_confirmation(setup,mutation):
    app,client=setup
    html=upload(client,archive({'dungeon.md':md('Dungeon','Dungeon'),
        'new.md':md('New module','Module')})).get_data(as_text=True)
    token=re.search(r'name="preview_id" value="([a-f0-9]+)"',html).group(1)
    with app.app_context():
        campaign=db.session.get(Campaign,1)
        if mutation=='delete':
            from app.lib.campaign_parties import delete_party
            for party in list(campaign.parties):
                delete_party(party)
            db.session.delete(campaign)
        else:
            campaign.owner_id=2
        db.session.commit()
    response=confirm(client,token)
    assert response.status_code==(404 if mutation=='delete' else 403)
    with app.app_context():
        assert not db.session.get(CampaignImport,token).consumed
        assert ContentEntry.query.count()==0


def test_archive_parents_take_priority_and_ids_never_resolve_existing_records(setup):
    app,client=setup
    html=upload(client,archive({'campaign.md':md('Secret campaign','Campaign'),
        'dungeon.md':md('Dungeon','Dungeon','Secret campaign')})).get_data(as_text=True)
    assert 'is not in this module' not in html  # The parent is the archive's own front page.
    token=re.search(r'name="preview_id" value="([a-f0-9]+)"',html).group(1)
    assert confirm(client,token).status_code==302
    with app.app_context():
        dungeon=ContentEntry.query.filter_by(title='Dungeon').one()
        assert dungeon.parent_id is None and dungeon.module.title=='Secret campaign'
    data=md('Another dungeon','Dungeon').replace('type: Dungeon\n','type: Dungeon\nparent_id: 1\n')
    html=upload(client,archive({'dungeon.md':data})).get_data(as_text=True)
    assert 'parent_id' in html and 'is missing' in html and 'name="preview_id"' not in html


def test_links_and_references_resolve_within_the_module(setup):
    app,client=setup
    files={'source.md':md('Source',body='See [[Target]].')
            .replace('layout: default\n','layout: default\nid: source\n'),
        'target.md':md('Target',parent='Somewhere else')
            .replace('layout: default\n','layout: default\nid: target\n')}
    with app.app_context():
        preview=preview_archive(archive(files),owner_id=1)
        assert not preview['errors']
        source=next(row for row in preview['rows'] if row['title']=='Source')
        assert source['references']
        files['manifest.json']=json.dumps({'format':'kettlewright-campaign','version':1,
            'links':[{'source':'source','target':'target'}]})
        assert not preview_archive(archive(files),owner_id=1)['errors']


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
    assert 'Module / My Campaign / Dungeon' in html and 'Unfiled' not in html
    assert 'image.png' in html
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    with app.app_context():
        assert ContentEntry.query.count() == 0
        assert Campaign.query.count() == 1
    login(client, 2)
    assert confirm(client, token).status_code == 404
    login(client, 1)
    assert confirm(client, token).status_code == 302
    with app.app_context():
        dungeon = ContentEntry.query.filter_by(title='Dungeon').one()
        room = ContentEntry.query.filter_by(title='Room').one()
        assert room.parent_id == dungeon.id
        assert room.campaign_id == dungeon.campaign_id
        assert dungeon.pointcrawl.kind == 'dungeon'
        assert dungeon.campaign_id == 1 and dungeon.module.title == 'My Campaign'
        dungeon_module = dungeon.module_id
        assert ContentEntry.query.filter_by(title='Loose').one().module_id == dungeon.module_id
        assert ContentEntry.query.filter_by(category='overview').one().body == 'A **private** description.'
        campaign_id = dungeon.campaign_id
    assert client.get('/party/1/materials/data').json == {'entries': []}
    assert 'Room' in client.get(f'/campaigns/{campaign_id}/modules/{dungeon_module}/').get_data(as_text=True)
    assert confirm(client, token).status_code == 409
    with app.app_context():
        assert Campaign.query.count() == 1  # Modules never create campaigns.


@pytest.mark.parametrize('files,expected', [
    ({'a.md': md('A', parent='B'), 'b.md': md('B', parent='A')}, 'cycle'),
    ({'a.md': md('A'), 'b.md': md('A'), 'c.md': md('C', parent='A')}, 'ambiguous'),
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


def test_import_is_available_without_tester_ids(setup):
    app, client = setup
    app.config['FEATURE_TEST_USER_IDS'] = set()
    assert client.get('/materials/import-archive').status_code == 200
    assert upload(client, archive({'a.md': md('A')})).status_code == 200


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
    with app.app_context():
        db.session.add(Campaign(id=2, owner_id=1, name='Elsewhere'))
        db.session.commit()
    response = upload(client, archive({'root.md': md('Root'), 'child.md': md('Child', parent='Root')}))
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', response.get_data(as_text=True)).group(1)
    confirm(client, token, campaign=2)
    with app.app_context():
        root = ContentEntry.query.filter_by(title='Root').one()
        root_id = root.id
    assert client.post(f'/materials/{root_id}/edit', data={'version': 1, 'title': 'Root',
        'body': 'changed', 'category': 'note', 'campaign_id': 1}).status_code == 302
    with app.app_context():
        child = ContentEntry.query.filter_by(title='Child').one()
        assert child.campaign_id == 1 and child.module.campaign_id == 1
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


def preview_token(html):
    return re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)


def test_module_front_page_and_adding_files_to_a_module(setup):
    app, client = setup
    html = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(md('Solo', 'Module').encode()), 'solo.md')}).get_data(as_text=True)
    assert 'Front page</strong> · solo.md · becomes an Overview article' in html
    assert confirm(client, preview_token(html)).status_code == 302
    with app.app_context():
        overview = ContentEntry.query.filter_by(title='Solo').one()
        assert overview.category == 'overview' and overview.module.title == 'Solo'
        module_id = overview.module_id
    html = client.post('/materials/import-archive', data={'module_id': module_id,
        'archive': (io.BytesIO(md('Cave', 'Dungeon').encode()), 'cave.md')}).get_data(as_text=True)
    assert 'Adding to the module Solo.' in html and f'name="module_id" value="{module_id}"' in html
    assert client.post('/materials/import-archive', data={'preview_id': preview_token(html),
                                                           'module_id': module_id}).status_code == 302
    with app.app_context():
        cave = ContentEntry.query.filter_by(title='Cave').one()
        assert cave.module_id == module_id and cave.category == 'dungeon'
        from app.models import Module
        assert Module.query.count() == 1


def test_inferred_rows_can_be_renamed_and_retyped_before_import(setup):
    app, client = setup
    files = {'kept.md': md('Kept', 'Note'), 'loose.md': '\n\n# Loose Notes\n\nBody text.'}
    html = upload(client, archive(files)).get_data(as_text=True)
    index = re.search(r'name="title_(\d+)" value="Loose Notes"', html).group(1)
    assert 'name="title_' + index + '"' in html and html.count('name="title_') == 1
    kept = str(1 - int(index))
    # Overrides for rows that had valid metadata are ignored.
    response = confirm(client, preview_token(html), **{
        f'title_{index}': 'Renamed', f'category_{index}': 'npc', f'title_{kept}': 'Ignored'})
    assert response.status_code == 302
    with app.app_context():
        entry = ContentEntry.query.filter_by(title='Renamed').one()
        assert entry.category == 'npc'
        assert 'Loose Notes' not in entry.body
        assert ContentEntry.query.filter_by(title='Kept').count() == 1


def test_invalid_override_rejects_without_importing(setup):
    app, client = setup
    html = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(b'plain'), 'plain.md')}).get_data(as_text=True)
    response = client.post('/materials/import-archive', data={'preview_id': preview_token(html), 'category_0': 'map'})
    assert response.status_code == 400
    with app.app_context():
        assert ContentEntry.query.count() == 0
        assert CampaignImport.query.filter_by(consumed=False).count() == 1


def test_inferred_body_errors_are_reported_not_dropped(setup):
    app, client = setup
    html = client.post('/materials/import-archive',
        data={'archive': (io.BytesIO(('x' * 60000).encode()), 'long.md')}).get_data(as_text=True)
    assert 'role="alert"' in html and 'name="preview_id"' not in html
