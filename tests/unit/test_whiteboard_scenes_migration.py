import importlib.util
from pathlib import Path
from copy import deepcopy
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text, MetaData, Table, select
from app.models import db


def test_one_alembic_head():
    config = Config()
    config.set_main_option('script_location', 'migrations')
    assert ScriptDirectory.from_config(config).get_heads() == ['375a01']


def test_upgrade_moves_legacy_tokens_preserves_images_and_downgrade():
    engine = create_engine('sqlite:///:memory:')
    db.metadata.create_all(engine)
    spec = importlib.util.spec_from_file_location('scenes_migration', Path('migrations/versions/375a01_whiteboard_scenes.py'))
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    import json
    image = {'id': 'f', 'mimeType': 'image/png', 'dataURL': 'kept byte for byte'}
    elements = [{'id': 'actor-1-one', 'type': 'image', 'fileId': 'f', 'x': 42, 'y': 17, 'width': 80, 'height': 80},
                {'id': 'actor-companion-10-monster', 'type': 'image', 'fileId': 'f'},
                {'id': 'actor-999-orphan', 'type': 'image', 'fileId': 'f'},
                {'id': 'background', 'type': 'rectangle', 'x': 100}]
    drawing = {'elements': deepcopy(elements), 'files': {'f': image}}
    fog = {'enabled': True, 'base': 'covered', 'strokes': [{'id': 'a'}], 'applied': ['a']}
    with engine.begin() as connection:
        for name in ('whiteboard_markers', 'whiteboard_tokens', 'whiteboard_scenes'):
            connection.execute(text(f'DROP TABLE {name}'))
        connection.execute(text('ALTER TABLE party_maps DROP COLUMN active_scene_id'))
        connection.execute(text('ALTER TABLE party_maps DROP COLUMN activation_version'))
        connection.execute(text("INSERT INTO users (id,username) VALUES (1,'warden'),(2,'player')"))
        connection.execute(text("INSERT INTO parties (id,owner,members,name,version) VALUES (1,1,'[1]','Party',0)"))
        connection.execute(text("INSERT INTO characters (id,owner,party_id,name,background,dead) VALUES (1,2,1,'Player','Test',0)"))
        connection.execute(text("INSERT INTO companions (id,kind,party_id,name,role,armor,attack,daily_cost,gold,notes,items,containers,shared) VALUES (10,'monster',1,'Goblin','Goblin',0,'',0,0,'secret','[]','[]',0)"))
        connection.execute(text('INSERT INTO party_maps (party_id,drawing,version,generation,fog,fog_version) VALUES (1,:drawing,7,3,:fog,4)'), {'drawing': json.dumps(drawing), 'fog': json.dumps(fog)})
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        meta = MetaData()
        scenes, tokens, boards = [Table(name, meta, autoload_with=connection) for name in ('whiteboard_scenes','whiteboard_tokens','party_maps')]
        scene = connection.execute(select(scenes)).mappings().one()
        assert (scene['version'], scene['generation'], scene['fog_version']) == (7,3,4)
        assert scene['fog'] == fog
        rows = connection.execute(select(tokens)).mappings().all()
        assert {row['actor_key'] for row in rows} == {'1','companion:10'}
        assert all(row['visible'] is True and row['files'] == {'f': image} for row in rows)
        assert scene['drawing']['elements'][0]['id'] == 'orphan-actor-999-orphan'
        assert connection.execute(select(boards)).mappings().one()['active_scene_id'] == scene['id']
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        restored = connection.execute(text('SELECT drawing,fog,version,generation FROM party_maps')).mappings().one()
        restored_drawing = json.loads(restored['drawing'])
        assert len(restored_drawing['elements']) == 4 and restored_drawing['files'] == drawing['files']
        assert json.loads(restored['fog']) == fog and restored['version'] == 7 and restored['generation'] == 3
