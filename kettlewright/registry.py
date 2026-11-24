"""The game systems the engine knows, by key, and the default one.

the engine's core has no system of its own. Systems live in packages outside it (Kettlewright's are in systems/ at
the root of the repository): each registers itself when its package is imported, and the package says which
one is the default. The packages are loaded on first use: KETTLEWRIGHT_SYSTEMS (comma-separated module names) or
'systems'.
"""
import importlib
import os

SYSTEMS = {}
_state = {'default': None, 'loaded': False}


def load(packages=None):
    """Import the system packages once, so their systems are registered."""
    if _state['loaded']:
        return
    _state['loaded'] = True
    names = packages or [name.strip() for name in os.environ.get('KETTLEWRIGHT_SYSTEMS', 'systems').split(',') if name.strip()]
    for name in names:
        importlib.import_module(name)


def register(game_system, default=False):
    """Add a system (from a system package, or a test). default: make it the default system."""
    SYSTEMS[game_system.key] = game_system
    if default or _state['default'] is None:
        _state['default'] = game_system.key
    return game_system


def set_default(key):
    """Make a registered system the default one (the one new campaigns, parties and characters play)."""
    if key not in SYSTEMS:
        raise KeyError(key)
    _state['default'] = key


def default_key():
    load()
    return _state['default']


def system(key=None):
    """The system with this key, or the default one. KeyError for an unknown key."""
    load()
    return SYSTEMS[key or _state['default']]


def system_or_default(key):
    """The system with this key, or the default one if there is no such system (any more)."""
    load()
    return SYSTEMS.get(key) or SYSTEMS[_state['default']]
