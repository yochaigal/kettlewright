from alembic.script import ScriptDirectory


def test_migrations_have_one_head():
    scripts = ScriptDirectory('migrations')

    assert len(scripts.get_heads()) == 1
