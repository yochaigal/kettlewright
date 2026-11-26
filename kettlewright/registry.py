"""The game system this Kettlewright instance plays: one per instance, chosen before it starts.

The engine's core has no system of its own. The systems live in packages outside it, under system/ at the root of
the repository (system/cairn for Cairn). GAME_SYSTEM, an environment variable (in .env), names the one this
instance plays; without it, the one system/__init__.py names as DEFAULT. On first use the engine imports system.<GAME_SYSTEM>, which registers its
GameSystem. Another system means another GAME_SYSTEM and a restart: everything the instance stores (campaigns,
parties, characters) plays the system it runs.
"""
import importlib
import os
from contextlib import contextmanager
from pathlib import Path

PACKAGE = 'system'  # The packages of the systems: system/<key>; system/__init__.py names the DEFAULT one.
_state = {'system': None}


class UnknownGameSystem(LookupError):
    """GAME_SYSTEM names no system in system/ (or its package registered none)."""


def configured_key():
    """The key GAME_SYSTEM names; the systems package's DEFAULT when it is not set."""
    key = os.environ.get('GAME_SYSTEM') or getattr(importlib.import_module(PACKAGE), 'DEFAULT', '')
    return key.strip().lower()


def available():
    """The systems an instance can play: the packages in system/."""
    module = importlib.import_module(PACKAGE)
    return sorted(path.parent.name for path in Path(module.__file__).parent.glob('*/__init__.py'))


def register(game_system):
    """Called by a system's package when it is imported. The instance plays it if it is the one GAME_SYSTEM names;
    a package imported for something else (its tables, a test) doesn't change the instance's system. Returns it."""
    if game_system.key == configured_key() and _state['system'] is None:
        _state['system'] = game_system
    return game_system


def load():
    """Import the package of the system GAME_SYSTEM names, once. UnknownGameSystem if there is no such system."""
    if _state['system'] is not None:
        return _state['system']
    key = configured_key()
    try:
        importlib.import_module(f'{PACKAGE}.{key}')
    except ModuleNotFoundError as error:
        if error.name not in (f'{PACKAGE}.{key}', PACKAGE):
            raise
        raise UnknownGameSystem(f"GAME_SYSTEM={key}: no such game system. Available: {', '.join(available())}.") from None
    if _state['system'] is None:
        raise UnknownGameSystem(f"system.{key} registered no game system with the key '{key}'.")
    return _state['system']


def system():
    """The game system this instance plays."""
    return _state['system'] or load()


@contextmanager
def use_system(game_system):
    """Play another system for a while (tests, tools); the instance's system again after."""
    before = system()
    _state['system'] = game_system
    try:
        yield game_system
    finally:
        _state['system'] = before
