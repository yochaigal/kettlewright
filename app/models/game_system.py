"""The game system a campaign, party or character plays (#487): set when it is created, then fixed.

Each has a game_system column (a kettlewright system's key). It can be given while the row is new; once saved, a
flush that changes it fails, so a campaign, party or character keeps its system until it is deleted.
"""
from sqlalchemy import event, inspect, select
from sqlalchemy.orm import Session

from kettlewright.registry import default_key


def GAME_SYSTEM_DEFAULT():
    """A new row's game system: the default one (systems/__init__.py)."""
    return default_key()


class GameSystemChanged(ValueError):
    """A saved campaign, party or character was given another game system."""


@event.listens_for(Session, 'before_flush')
def keep_game_systems(session, flush_context, instances):
    for obj in session.dirty:
        table = getattr(type(obj), '__table__', None)
        if table is None or 'game_system' not in table.columns:
            continue
        history = inspect(obj).attrs.game_system.history
        if not history.added:
            continue
        if history.deleted:
            saved = history.deleted[0]
        else:  # The old value wasn't loaded (an expired row): read what is stored.
            with session.no_autoflush:
                saved = session.execute(select(table.c.game_system).where(table.c.id == obj.id)).scalar()
        if saved is not None and saved != history.added[0]:
            raise GameSystemChanged(f'{type(obj).__name__} {obj.id} keeps its game system ({saved}).')
