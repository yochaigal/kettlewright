from flask_migrate import upgrade, downgrade
from sqlalchemy import inspect, text
from app.models import db


def test_campaign_migration_preserves_existing_parties_and_matches_models(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'migration.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='124a01')
        db.session.execute(text("INSERT INTO users (id, username) VALUES (1, 'existing')"))
        db.session.execute(text("INSERT INTO parties (id, owner, name, version) VALUES (1, 1, 'Existing party', 0)"))
        db.session.commit()
        upgrade()
        inspector = inspect(db.engine)
        names = ('campaigns','campaign_parties','content_entries','content_links','party_presentations',
                 'pointcrawl_maps','map_nodes','map_edges')
        for name in names:
            assert {c['name'] for c in inspector.get_columns(name)} == set(db.metadata.tables[name].columns.keys())
        assert db.session.execute(text('SELECT name FROM parties WHERE id=1')).scalar() == 'Existing party'
        assert db.session.execute(text('SELECT count(*) FROM campaigns')).scalar() == 0
        db.session.commit()
        downgrade(revision='124a01')
        assert 'campaigns' not in inspect(db.engine).get_table_names()
        assert db.session.execute(text('SELECT name FROM parties WHERE id=1')).scalar() == 'Existing party'
