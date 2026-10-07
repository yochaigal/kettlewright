import io
import json
import zipfile

from flask_migrate import upgrade, downgrade
from sqlalchemy import inspect, text

from app.lib.article_references import tokens, headings, private_reference_urls
from app.lib.campaign_import import preview_archive, import_preview
from app.lib.rich_content import render_content
from app.models import db, ContentEntry, Campaign, PartyPresentation
from test_campaigns import setup, create_entry, login, reveal
from test_campaign_import import archive, md


def test_wiki_parser_code_aliases_paths_and_headings():
    body = '[[Village|home]] [Road](folder/Road.md#History) `[[Hidden]]`\n\n```md\n[[Secret]]\n```\n![[Embed]]'
    assert tokens(body) == ['Village', 'folder/Road.md#History']
    rendered = str(render_content(body, {'Village': '/materials/1/edit',
        'folder/Road.md#History': '/materials/2/edit#kw-h-history'}))
    assert '>home</a>' in rendered and 'href="/materials/2/edit#kw-h-history"' in rendered
    assert '<code>[[Hidden]]</code>' in rendered and '![[Embed]]' in rendered
    assert 'href="/materials/3' not in rendered
    assert headings('## Зима и **снег**\n\n## Зима и **снег**') == [
        {'title': 'Зима и снег', 'path': 'Зима и снег', 'anchor': 'kw-h-зима-и-снег'},
        {'title': 'Зима и снег', 'path': 'Зима и снег', 'anchor': 'kw-h-зима-и-снег-2'}]
    assert 'id="kw-h-зима-и-снег-2"' in str(render_content('## Зима и **снег**\n\n## Зима и **снег**'))


def test_stable_bindings_rename_and_editor_preview(setup):
    app, client = setup
    target = create_entry(client, title='Village')
    source = create_entry(client, title='Letter')
    assert client.post(f'/materials/{source}/edit', data={'version': 1, 'title': 'Letter',
        'body': '[[Village|home]]', 'category': 'note', 'campaign_id': 1}).status_code == 302
    with app.app_context():
        assert db.session.get(ContentEntry, source).references == {'Village': db.session.get(ContentEntry, target).reference_key}
    assert client.post(f'/materials/{target}/edit', data={'version': 1, 'title': 'Renamed village',
        'body': '## History\n\nPrivate history.', 'category': 'note', 'campaign_id': 1}).status_code == 302
    rendered = client.get(f'/materials/{source}/preview').get_data(as_text=True)
    assert f'href="/materials/{target}/edit"' in rendered and '>home</a>' in rendered
    preview = client.post('/materials/reference-preview', data={'entry_id': source, 'campaign_id': 1,
        'body': '[[Village|home]]'}).json
    assert f'href="/materials/{target}/edit"' in preview['html']
    catalog = client.get('/materials/reference-catalog?campaign_id=1').json['articles']
    renamed = next(item for item in catalog if item['id'] == target)
    assert renamed['title'] == 'Renamed village'
    assert renamed['headings'] == [{'title': 'History', 'path': 'History', 'anchor': 'kw-h-history'}]
    login(client, 2)
    assert client.get('/materials/reference-catalog?campaign_id=1').status_code == 403
    assert client.post('/materials/reference-preview', data={'entry_id': source, 'body': '[[Village]]'}).status_code == 403


def test_player_links_only_published_targets_and_headings(setup):
    app, client = setup
    target = create_entry(client, title='Village')
    source = create_entry(client, title='Letter')
    with app.app_context():
        db.session.get(ContentEntry, target).body = '## Secret heading\nPRIVATE SECRET'
        db.session.get(ContentEntry, source).body = '[[Village|home]] [[Village#Secret heading|history]]'
        db.session.commit()
    assert reveal(client, source, body='[[Village|home]] [[Village#Secret heading|history]]').status_code == 302
    login(client, 2)
    hidden = client.get(f'/party/1/materials/{source}').get_data(as_text=True)
    assert 'home' in hidden and f'/party/1/materials/{target}' not in hidden
    assert 'PRIVATE SECRET' not in hidden
    login(client, 1)
    assert reveal(client, target, title='Public village', body='## Public heading\nPublic history.').status_code == 302
    login(client, 2)
    shown = client.get(f'/party/1/materials/{source}').get_data(as_text=True)
    assert f'href="/party/1/materials/{target}"' in shown
    assert '#kw-h-secret-heading' not in shown and '/materials/' + str(target) + '/edit' not in shown
    assert client.get(f'/party/1/materials/{target}/preview').status_code == 200
    assert 'PRIVATE SECRET' not in client.get(f'/party/1/materials/{target}/preview').get_data(as_text=True)
    login(client, 3)
    assert client.get(f'/party/2/materials/{target}/preview').status_code == 404
    login(client, 1)
    assert client.post(f'/materials/{target}/revoke/1', data={'version': 1}).status_code == 302
    login(client, 2)
    assert f'/party/1/materials/{target}' not in client.get(f'/party/1/materials/{source}').get_data(as_text=True)


def test_published_bindings_do_not_follow_original_edits(setup):
    app, client = setup
    first = create_entry(client, title='First')
    second = create_entry(client, title='Second')
    source = create_entry(client, title='Source')
    with app.app_context():
        db.session.get(ContentEntry, source).body = '[[First]]'
        db.session.commit()
    assert reveal(client, source, body='[[First]]').status_code == 302
    with app.app_context():
        original = db.session.get(ContentEntry, source)
        original.body = '[[Second]]'
        db.session.commit()
        assert original.references == {'Second': db.session.get(ContentEntry, second).reference_key}
        assert PartyPresentation.query.filter_by(entry_id=source, party_id=1).one().references == {'First': db.session.get(ContentEntry, first).reference_key}


def test_import_export_preserves_relative_paths_and_renamed_bindings(setup):
    app, client = setup
    files = {'campaign.md': md('Campaign', 'Campaign'),
        'places/Village.md': md('Village', 'Settlement', 'Campaign', '## History\nOld bridge.'),
        'notes/Letter.md': md('Letter', 'Note', 'Campaign',
            '[[../places/Village#History|home]] [visit](../places/Village.md) [[Missing]]')}
    with app.app_context():
        preview = preview_archive(archive(files))
        assert preview['errors'] == []
        assert any('Missing' in warning for warning in preview['warnings'])
        import_preview(preview, 1)
        db.session.commit()
        source = ContentEntry.query.filter_by(title='Letter').one()
        target = ContentEntry.query.filter_by(title='Village').one()
        target.title = 'Renamed village'
        db.session.commit()
        assert source.references == {'../places/Village#History': target.reference_key, '../places/Village.md': target.reference_key}
        campaign_id = source.campaign_id
    response = client.get(f'/campaigns/{campaign_id}/export')
    with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
        manifest = json.loads(exported.read('manifest.json'))
        assert len(manifest['references']) == 2
        assert 'places/Village.md' in exported.namelist()
    with app.app_context():
        payload = preview_archive(response.data)
        assert payload['errors'] == []
        import_preview(payload, 2)
        db.session.commit()
        source = ContentEntry.query.filter_by(owner_id=2, title='Letter').one()
        target = ContentEntry.query.filter_by(owner_id=2, title='Renamed village').one()
        assert set(source.references.values()) == {target.reference_key}
        assert '#kw-h-history' in private_reference_urls(source)['../places/Village#History']


def test_ambiguous_and_unavailable_links_stay_plain_text(setup):
    app, client = setup
    create_entry(client, title='Same')
    create_entry(client, title='Same')
    source = create_entry(client, title='Source')
    preview = client.post('/materials/reference-preview', data={'entry_id': source, 'campaign_id': 1,
        'body': '[[Same]] [[Missing]] [unsafe](/materials/999/edit)'}).json
    assert preview['references'] == {} and '<a ' not in preview['html']
    assert 'Same' in preview['unresolved']


def test_reference_migration_single_head_and_downgrade(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'references.sqlite'))
    from app import create_app
    from alembic.script import ScriptDirectory
    assert ScriptDirectory('migrations').get_heads() == ['336a01']
    app = create_app()
    with app.app_context():
        upgrade(revision='335a01')
        db.session.execute(text("INSERT INTO users (id,username) VALUES (1,'owner')"))
        db.session.execute(text("INSERT INTO content_entries (id,owner_id,category,title,body,path_type,version) VALUES (1,1,'note','Old','[[Old]]','standard',1)"))
        db.session.commit()
        upgrade()
        row = db.session.get(ContentEntry, 1)
        assert row.body == '[[Old]]' and row.references == {} and row.source_path == 'articles/Old.md'
        db.session.remove()
        downgrade(revision='335a01')
        assert 'references' not in {column['name'] for column in inspect(db.engine).get_columns('content_entries')}
