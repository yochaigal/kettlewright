import io
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
