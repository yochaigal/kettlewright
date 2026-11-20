"""500a01: every existing party is filed under one of its Warden's campaigns."""
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text

from app.models import db


def test_parties_are_filed_under_a_campaign(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'parties.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='430a01')
        run = lambda sql: db.session.execute(text(sql))
        run("INSERT INTO users (id, username) VALUES (1, 'warden'), (2, 'other')")
        run("INSERT INTO campaigns (id, owner_id, name, version) VALUES (1, 1, 'Old', 1), (2, 1, 'Main', 1), (3, 2, 'Theirs', 1)")
        run("INSERT INTO parties (id, owner, name, version) VALUES "
            "(1, 1, 'Shown', 0), (2, 1, 'Linked', 0), (3, 1, 'Alone', 0), (4, NULL, 'Orphan', 0)")
        run("INSERT INTO content_entries (id, owner_id, campaign_id, category, title, body, path_type, version, "
            "source_path, reference_key, \"references\", is_heart) VALUES "
            "(1, 1, 1, 'npc', 'A', '', 'standard', 1, '', 'k1', '{}', 0), "
            "(2, 1, 2, 'npc', 'B', '', 'standard', 1, '', 'k2', '{}', 0), "
            "(3, 1, 2, 'npc', 'C', '', 'standard', 1, '', 'k3', '{}', 0), "
            "(4, 2, 3, 'npc', 'D', '', 'standard', 1, '', 'k4', '{}', 0)")
        # Party 1 was shown one article of Old and two of Main (and one of someone else's campaign).
        run("INSERT INTO party_presentations (id, entry_id, party_id, title, body, path_type, published, version, \"references\") VALUES "
            "(1, 1, 1, 'A', '', 'standard', 1, 1, '{}'), (2, 2, 1, 'B', '', 'standard', 1, 1, '{}'), "
            "(3, 3, 1, 'C', '', 'standard', 1, 1, '{}'), (4, 4, 1, 'D', '', 'standard', 1, 1, '{}')")
        run("INSERT INTO campaign_parties (campaign_id, party_id) VALUES (1, 2), (3, 2)")
        db.session.commit()

        upgrade(revision='500a01')
        rows = dict(run('SELECT p.name, c.name FROM parties p LEFT JOIN campaigns c ON c.id = p.campaign_id').all())
        assert rows == {'Shown': 'Main',      # Shown the most articles from it.
                        'Linked': 'Old',      # Its old link to one of its Warden's campaigns.
                        'Alone': 'Alone',     # A new campaign named after it.
                        'Orphan': None}       # No Warden, nothing to file it under.
        assert run("SELECT owner_id, official_backgrounds, modules FROM campaigns WHERE name = 'Alone'").one() == (1, 1, '[]')
        assert 'campaign_parties' not in inspect(db.engine).get_table_names()
        db.session.commit()

        downgrade(revision='430a01')
        assert sorted(run('SELECT campaign_id, party_id FROM campaign_parties').all()) == [(1, 2), (2, 1), (4, 3)]
        assert 'campaign_id' not in {c['name'] for c in inspect(db.engine).get_columns('parties')}


def test_modules_one_party_and_no_unfiled_articles(tmp_path, monkeypatch):
    """501a01: articles go into modules, unfiled ones into a campaign, and every campaign has a party."""
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'modules.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='500a01')
        run = lambda sql: db.session.execute(text(sql))
        run("INSERT INTO users (id, username) VALUES (1, 'warden')")
        run("INSERT INTO campaigns (id, owner_id, name, version, official_backgrounds, modules, backgrounds) VALUES "
            "(1, 1, 'Marches', 1, 1, '[{\"slug\": \"cas-1\", \"title\": \"Marches\"}, {\"slug\": \"cas-2\", \"title\": \"CAS-2\"}]', "
            "'{\"Tidewatcher\": {\"names\": [\"Mara\"]}}'), (2, 1, 'Empty', 1, 1, '[]', NULL)")
        run("INSERT INTO parties (id, owner, owner_username, name, version, campaign_id, party_url) VALUES "
            "(1, 1, 'warden', 'First', 0, 1, 'first'), (2, 1, 'warden', 'Second', 0, 1, 'second')")
        entry = ("INSERT INTO content_entries (id, owner_id, campaign_id, category, title, body, path_type, version, "
                 "source_path, reference_key, \"references\", is_heart) VALUES ")
        run(entry + "(1, 1, 1, 'npc', 'In campaign', '', 'standard', 1, '', 'k1', '{}', 0), "
                    "(2, 1, NULL, 'note', 'Loose', '', 'standard', 1, '', 'k2', '{}', 0), "
                    "(3, 1, NULL, 'party_note', 'Party only', '', 'standard', 1, '', 'k3', '{}', 0)")
        db.session.commit()

        upgrade()
        campaigns = {name: id for id, name in run('SELECT id, name FROM campaigns').all()}
        assert set(campaigns) == {'Marches', 'Empty', 'Unfiled articles'}
        parties = sorted(run('SELECT c.name, p.name FROM campaigns c JOIN parties p ON p.campaign_id = c.id').all())
        assert parties == [('Empty', 'Empty'), ('Marches', 'First'), ('Marches', 'Second'),  # Several stay together.
                           ('Unfiled articles', 'Unfiled articles')]
        created = run("SELECT join_code, party_url, owner_username, members FROM parties WHERE name IN ('Empty', 'Unfiled articles')").all()
        assert len(created) == 2 and all(code and url and user == 'warden' and members == '[]' for code, url, user, members in created)
        modules = run('SELECT campaign_id, title, slug, backgrounds FROM modules ORDER BY id').all()
        assert [(m[0], m[1], m[2]) for m in modules] == [(campaigns['Marches'], 'Marches', 'cas-1'),  # Started from cas-1.
                                                         (campaigns['Unfiled articles'], 'Unfiled articles', '')]
        assert 'Tidewatcher' in modules[0][3]
        filed = dict(run('SELECT title, module_id IS NOT NULL FROM content_entries').all())
        assert filed == {'In campaign': 1, 'Loose': 1, 'Party only': 0}  # Party notes stay with their party.
        assert run("SELECT campaign_id FROM content_entries WHERE title = 'Loose'").scalar() == campaigns['Unfiled articles']
        columns = {c['name'] for c in inspect(db.engine).get_columns('campaigns')}
        assert 'backgrounds' not in columns and 'modules' not in columns
        db.session.commit()

        downgrade(revision='500a01')
        assert 'modules' not in inspect(db.engine).get_table_names()
        assert 'Tidewatcher' in run("SELECT backgrounds FROM campaigns WHERE name = 'Marches'").scalar()


def test_party_versions_become_party_notes(tmp_path, monkeypatch):
    """502a01: a party copy that differs from its article becomes a party note; the article is hidden from it."""
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'versions.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='501a01')
        run = lambda sql: db.session.execute(text(sql))
        run("INSERT INTO users (id, username) VALUES (1, 'warden')")
        run("INSERT INTO campaigns (id, owner_id, name, version, official_backgrounds) VALUES (1, 1, 'C', 1, 1)")
        run("INSERT INTO parties (id, owner, name, version, campaign_id) VALUES (1, 1, 'P', 0, 1)")
        entry = ("INSERT INTO content_entries (id, owner_id, campaign_id, category, title, body, path_type, version, "
                 "source_path, reference_key, \"references\", is_heart) VALUES ")
        run(entry + "(1, 1, 1, 'npc', 'Secret name', 'Secret body', 'hidden', 1, '', 'k1', '{\"A\": \"k2\"}', 0), "
                    "(2, 1, 1, 'npc', 'Same', 'Same body', 'standard', 1, '', 'k2', '{}', 0)")
        run("INSERT INTO party_presentations (id, entry_id, party_id, title, body, path_type, published, version, \"references\") "
            "VALUES (1, 1, 1, 'Rumour', 'What they heard', 'standard', 1, 1, '{}'), "
            "(2, 2, 1, 'Same', 'Same body', 'standard', 1, 1, '{}')")
        db.session.commit()

        upgrade(revision='502a01')
        shown = run('SELECT p.entry_id, p.title, p.body, e.category FROM party_presentations p '
                    'JOIN content_entries e ON e.id = p.entry_id ORDER BY p.entry_id').all()
        assert [(row[0], row[1], row[3]) for row in shown] == [(2, 'Same', 'npc'), (3, 'Rumour', 'party_note')]
        assert shown[1][2] == 'What they heard'  # Exactly what the party knew; the secret never reaches it.
        note = run("SELECT owner_id, campaign_id, module_id FROM content_entries WHERE id = 3").one()
        assert note == (1, None, None)
        assert 'Secret' not in str(run('SELECT title, body FROM party_presentations').all())


def test_maps_apart_drops_snapshots_and_empty_point_canvases(tmp_path, monkeypatch):
    """504a01: revealed maps show their current drawing; empty canvases on points and sub-articles go."""
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'maps.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='503a01')
        run = lambda sql: db.session.execute(text(sql))
        run("INSERT INTO users (id, username) VALUES (1, 'warden')")
        run("INSERT INTO campaigns (id, owner_id, name, version, official_backgrounds) VALUES (1, 1, 'C', 1, 1)")
        run("INSERT INTO parties (id, owner, name, version, campaign_id) VALUES (1, 1, 'P', 0, 1)")
        entry = ("INSERT INTO content_entries (id, owner_id, campaign_id, category, title, body, path_type, version, "
                 "source_path, reference_key, \"references\", is_heart, parent_id) VALUES ")
        run(entry + "(1, 1, 1, 'realm', 'Realm', '', 'standard', 1, '', 'k1', '{}', 0, NULL), "
                    "(2, 1, 1, 'settlement', 'Town on the map', '', 'standard', 1, '', 'k2', '{}', 0, NULL), "
                    "(3, 1, 1, 'terrain', 'Sub-article', '', 'standard', 1, '', 'k3', '{}', 0, 1), "
                    "(4, 1, 1, 'topography', 'Blank map I made', '', 'standard', 1, '', 'k4', '{}', 0, NULL), "
                    "(5, 1, 1, 'dungeon', 'Drawn dungeon', '', 'standard', 1, '', 'k5', '{}', 0, 1)")
        run("INSERT INTO pointcrawl_maps (id, entry_id, kind, drawing, version) VALUES "
            "(1, 1, 'realm', NULL, 1), (2, 2, 'freeform', '{\"elements\": [], \"files\": {}}', 1), "
            "(3, 3, 'freeform', NULL, 1), (4, 4, 'freeform', NULL, 1), "
            "(5, 5, 'dungeon', '{\"elements\": [{\"id\": \"a\"}], \"files\": {}}', 1)")
        run("INSERT INTO map_nodes (id, map_id, entry_id, number, x, y, nested_map_id) VALUES (1, 1, 2, 1, 0, 0, 2)")
        run("INSERT INTO party_presentations (id, entry_id, party_id, title, body, path_type, published, version, "
            "\"references\", drawing) VALUES (1, 1, 1, 'Realm', '', 'standard', 1, 1, '{}', '{\"elements\": []}')")
        db.session.commit()

        upgrade(revision='504a01')
        kept = sorted(row[0] for row in run('SELECT entry_id FROM pointcrawl_maps'))
        assert kept == [1, 4, 5]  # The realm, a map someone made, and a drawn one.
        assert run('SELECT nested_map_id FROM map_nodes WHERE id = 1').scalar() is None
        assert 'drawing' not in {c['name'] for c in inspect(db.engine).get_columns('party_presentations')}
        db.session.commit()

        downgrade(revision='503a01')
        assert 'drawing' in {c['name'] for c in inspect(db.engine).get_columns('party_presentations')}


def test_backgrounds_setting_moves_to_each_party(tmp_path, monkeypatch):
    """505a01: a campaign's "official backgrounds" setting becomes each of its parties' setting."""
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'backgrounds.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='504a01')
        run = lambda sql: db.session.execute(text(sql))
        run("INSERT INTO users (id, username) VALUES (1, 'warden')")
        run("INSERT INTO campaigns (id, owner_id, name, version, official_backgrounds) VALUES "
            "(1, 1, 'Hidden', 1, 0), (2, 1, 'Shown', 1, 1)")
        run("INSERT INTO parties (id, owner, name, version, campaign_id) VALUES "
            "(1, 1, 'A', 0, 1), (2, 1, 'B', 0, 1), (3, 1, 'C', 0, 2), (4, 1, 'Loose', 0, NULL)")
        db.session.commit()
        upgrade(revision='505a01')
        assert dict(run('SELECT name, official_backgrounds FROM parties').all()) == {'A': 0, 'B': 0, 'C': 1, 'Loose': 1}
        assert 'official_backgrounds' not in {c['name'] for c in inspect(db.engine).get_columns('campaigns')}
        db.session.commit()
        downgrade(revision='504a01')
        assert dict(run('SELECT name, official_backgrounds FROM campaigns').all()) == {'Hidden': 0, 'Shown': 1}
