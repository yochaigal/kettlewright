"""A module's front page is its description (shown first in its wiki), not an article named after it."""
import io
import zipfile

from flask_migrate import upgrade
from sqlalchemy import text

from app.lib.campaign_export import export_module
from app.models import db, Campaign, ContentEntry, Module, User


def setup_module_page(app_with_babel, description=''):
    app = app_with_babel
    with app.app_context():
        db.session.add(User(id=1, username='warden', email='warden@example.com'))
        campaign = Campaign(id=7, owner_id=1, name='Homebrew')
        module = Module(id=3, campaign=campaign, title='Twin Lakes', description=description)
        db.session.add_all([campaign, module, ContentEntry(owner_id=1, campaign=campaign, module=module,
                                                           category='npc', title='Reeve', body='Stern.')])
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    return app, client


def test_settings_save_the_description_and_the_wiki_shows_it_first(app_with_babel):
    app, client = setup_module_page(app_with_babel)
    page = client.get('/campaigns/7/modules/3/').get_data(as_text=True)
    assert 'Module settings' in page and 'name="description"' in page
    assert client.post('/campaigns/7/modules/3/', data={'version': '1', 'name': 'Twin Lakes',
                                                        'description': 'Buy it in **print**.'}).status_code == 302
    with app.app_context():
        assert db.session.get(Module, 3).description == 'Buy it in **print**.'
    wiki = client.get('/campaigns/7/modules/3/wiki/').get_data(as_text=True)
    assert 'wiki-intro' in wiki and 'Buy it in <strong>print</strong>.' in wiki
    assert 'Open article' not in wiki  # It is not an article.
    # A rename alone (no description field sent) keeps it.
    client.post('/campaigns/7/modules/3/', data={'version': '2', 'name': 'Twin Lakes 2'})
    with app.app_context():
        assert db.session.get(Module, 3).description == 'Buy it in **print**.'


def test_an_empty_module_has_no_intro(app_with_babel):
    app, client = setup_module_page(app_with_babel)
    assert 'wiki-intro' not in client.get('/campaigns/7/modules/3/wiki/').get_data(as_text=True)


def test_export_writes_the_description_as_module_md_and_the_cover_comes_from_it(app_with_babel):
    app, client = setup_module_page(app_with_babel, 'The **front** page.\n\n![Cover](https://example.com/cover.webp)')
    with app.app_context():
        archive = zipfile.ZipFile(export_module(db.session.get(Module, 3)))
        front = archive.read('module.md').decode()
        assert 'title: Twin Lakes' in front and 'The **front** page.' in front
        assert [name for name in archive.namelist() if name.startswith('articles/')] == ['articles/Reeve.md']
    cover = client.get('/campaigns/7/modules/3/cover')
    assert cover.status_code == 302 and cover.location == 'https://example.com/cover.webp'


def test_migration_moves_only_front_pages_nothing_depends_on(tmp_path, monkeypatch):
    """512a01: an Overview named after its module becomes the module's description, unless something
    visible depends on it. Revealed (Reveal module reveals it too) or related, it still moves."""
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'description.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='511a01')
        run = lambda sql, **values: db.session.execute(text(sql), values)
        run("INSERT INTO users (id, username) VALUES (1, 'warden')")
        run("INSERT INTO campaigns (id, owner_id, name, version) VALUES (1, 1, 'Home', 1)")
        run("INSERT INTO parties (id, owner, name, version, campaign_id) VALUES (1, 1, 'Party', 0, 1)")
        run("INSERT INTO modules (id, campaign_id, title, version) VALUES "
            "(1, 1, 'Plain', 1), (2, 1, 'Revealed', 1), (3, 1, 'Parent', 1), (4, 1, 'Linked', 1), (5, 1, 'Pictured', 1), "
            "(6, 1, 'Related', 1)")
        entries = [  # id, module, category, title, parent, image, references
            (1, 1, 'overview', 'Plain', None, '', '{}'), (2, 1, 'npc', 'Reeve', None, '', '{}'),
            (3, 2, 'overview', 'Revealed', None, '', '{}'),
            (4, 3, 'overview', 'Parent', None, '', '{}'), (5, 3, 'npc', 'Child', 4, '', '{}'),
            (6, 4, 'overview', 'Linked', None, '', '{}'), (7, 4, 'npc', 'Linker', None, '', '{"[[Linked]]": "k6"}'),
            (8, 5, 'overview', 'Pictured', None, 'own.webp', '{}'),
            (9, 6, 'overview', 'Related', None, '', '{}'), (10, 6, 'npc', 'Relative', None, '', '{}'),
        ]
        for entry_id, module_id, category, title, parent, image, references in entries:
            run('INSERT INTO content_entries (id, owner_id, campaign_id, module_id, parent_id, category, title, body, '
                'path_type, version, source_path, reference_key, "references", is_heart, image) VALUES '
                "(:id, 1, 1, :module, :parent, :category, :title, :body, 'standard', 1, '', :key, :refs, 0, :image)",
                id=entry_id, module=module_id, parent=parent, category=category, title=title,
                body=f'Front of {title}.', key=f'k{entry_id}', refs=references, image=image)
        run("INSERT INTO party_presentations (id, entry_id, party_id, title, body, path_type, published, version, "
            "\"references\") VALUES (1, 3, 1, 'Revealed', '', 'standard', 1, 1, '{}'), (2, 2, 1, 'Reeve', '', 'standard', 1, 1, '{}')")
        run('INSERT INTO content_links (source_id, target_id) VALUES (10, 9)')
        run("INSERT INTO stars (id, user_id, kind, target_id, name) VALUES (1, 1, 'article', 1, 'Plain')")
        db.session.commit()

        upgrade(revision='512a01')
        descriptions = dict(run('SELECT title, description FROM modules').all())
        assert descriptions == {'Plain': 'Front of Plain.', 'Revealed': 'Front of Revealed.', 'Related': 'Front of Related.',
                                'Parent': '', 'Linked': '', 'Pictured': ''}  # Sub-article, [[link]], own picture: kept.
        assert sorted(row[0] for row in run('SELECT id FROM content_entries').all()) == [2, 4, 5, 6, 7, 8, 10]
        assert run('SELECT COUNT(*) FROM stars').scalar() == 0
        assert run('SELECT entry_id FROM party_presentations').all() == [(2,)]  # The party keeps its other articles.
        assert run('SELECT COUNT(*) FROM content_links').scalar() == 0
