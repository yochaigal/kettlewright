from flask_migrate import upgrade, downgrade
from sqlalchemy import inspect, text
from app.models import db


def test_resource_labels_preserve_custom_titles_and_published_copies(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'resources.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='323a01')
        db.session.execute(text("INSERT INTO users (id,username) VALUES (1,'owner')"))
        db.session.execute(text("INSERT INTO parties (id,owner,name,version) VALUES (1,1,'Party',1)"))
        body = '**Abundance:** Fuel\n\n**Scarcity:** Livestock'
        examples = [
            ('resources', 'Fuel · Scarce: Livestock', body, 'Abundance: Fuel · Scarcity: Livestock'),
            ('resources', 'Our supplies', body, 'Our supplies'),
            ('resources', 'Fuel · Scarce: Livestock', 'Handwritten notes', 'Fuel · Scarce: Livestock'),
            ('custom', 'Fuel · Scarce: Livestock', body, 'Fuel · Scarce: Livestock'),
            ('resources', 'Fuel · Scarce: Livestock', '**Abundance:** Fuel', 'Fuel · Scarce: Livestock'),
            ('resources', ('A' * 190 + ' · Scarce: Land')[:200],
             '**Abundance:** ' + 'A' * 190 + '\n\n**Scarcity:** Land', ('Abundance: ' + 'A' * 190 + ' · Scarcity: Land')[:200]),
        ]
        for entry_id, (category, title, description, _) in enumerate(examples, 1):
            db.session.execute(text(
                "INSERT INTO content_entries (id,owner_id,category,title,body,path_type,version) "
                "VALUES (:id,1,:category,:title,:body,'standard',1)"
            ), {'id': entry_id, 'category': category, 'title': title, 'body': description})
        db.session.execute(text(
            "INSERT INTO party_presentations (entry_id,party_id,title,body,path_type,published,version) "
            "VALUES (1,1,'Known supplies','Known details','standard',1,1)"
        ))
        db.session.commit()
        upgrade()
        rows = db.session.execute(text('SELECT title,body,version FROM content_entries ORDER BY id')).all()
        for row, (_, original, description, expected) in zip(rows, examples):
            assert row.title == expected
            assert row.body == description
            assert row.version == (2 if original != expected else 1)
        published = db.session.execute(text('SELECT title,body,version FROM party_presentations')).one()
        assert tuple(published) == ('Known supplies', 'Known details', 1)


def test_descriptive_titles_migration_preserves_custom_titles_and_bodies(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'titles.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='322a01')
        db.session.execute(text("INSERT INTO users (id,username) VALUES (1,'owner')"))
        examples = [
            ('culture','Culture','**Character:** Struggling\n\n**Ambition:** Conversion','Struggling · Conversion'),
            ('resources','Resources','**Abundance:** Gemstones\n\n**Scarcity:** Land','Abundance: Gemstones · Scarcity: Land'),
            ('faction_type','Faction types','**Type:** Commoners\n\n**Agent:** Gravedigger','Commoners · Gravedigger'),
            ('faction_trait','Faction traits','**Trait 1:** Connected\n\n**Trait 2:** Selfish','Connected · Selfish'),
            ('advantage','Advantages','**Advantages:** Apparatus, Information','Apparatus, Information'),
            ('agenda','Agendas','**Agenda:** Explore Uncharted Lands','Explore Uncharted Lands'),
            ('culture','My people','**Character:** Hardy\n\n**Ambition:** Freedom','My people'),
            ('culture','Culture','Handwritten notes','Culture'),
        ]
        for i,(category,title,body,_) in enumerate(examples,1):
            db.session.execute(text('INSERT INTO content_entries (id,owner_id,category,title,body,path_type,version) VALUES (:id,1,:category,:title,:body,\'standard\',1)'),
                               {'id':i,'category':category,'title':title,'body':body})
        db.session.commit()
        upgrade()
        rows = db.session.execute(text('SELECT title,body,version FROM content_entries ORDER BY id')).all()
        for row,(_,original,body,expected) in zip(rows,examples):
            assert row.title == expected
            assert row.body == body
            assert row.version == (3 if original == 'Resources' else 2 if original != expected else 1)


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
                 'pointcrawl_maps','map_nodes','map_edges','campaign_imports')
        for name in names:
            assert {c['name'] for c in inspector.get_columns(name)} == set(db.metadata.tables[name].columns.keys())
        assert db.session.execute(text('SELECT name FROM parties WHERE id=1')).scalar() == 'Existing party'
        assert db.session.execute(text('SELECT count(*) FROM campaigns')).scalar() == 0
        db.session.commit()
        downgrade(revision='124a01')
        assert 'campaigns' not in inspect(db.engine).get_table_names()
        assert db.session.execute(text('SELECT name FROM parties WHERE id=1')).scalar() == 'Existing party'


def test_typed_migration_preserves_content_and_infers_only_explicit_types(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(tmp_path / 'typed.sqlite'))
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade(revision='320a01')
        db.session.execute(text("INSERT INTO users (id,username) VALUES (1,'owner')"))
        for entry_id, category, title in [(1,'location','Heart · Settlement: Village'),
                                         (2,'location','Forest: Ancient'),(3,'location','User title'),(4,'map','Old map')]:
            db.session.execute(text('INSERT INTO content_entries (id,owner_id,category,title,body,path_type,version) VALUES (:id,1,:category,:title,\'Preserved prose\',\'standard\',1)'),
                               {'id':entry_id,'category':category,'title':title})
        db.session.execute(text("INSERT INTO pointcrawl_maps (id,entry_id,kind,version) VALUES (1,4,'realm',1)"))
        db.session.commit()
        upgrade()
        rows=db.session.execute(text('SELECT category,is_heart,body FROM content_entries ORDER BY id')).all()
        assert [(row[0],bool(row[1])) for row in rows] == [('settlement',True),('forest',False),('custom',False),('realm',False)]
        assert all(row[2] == 'Preserved prose' for row in rows)
        db.session.commit()
        downgrade(revision='320a01')
        assert 'is_heart' not in {column['name'] for column in inspect(db.engine).get_columns('content_entries')}
