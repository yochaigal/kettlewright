"""A game system's tables (backgrounds, traits, the bestiary, the Warden's generators...): JSON files in its package.

    rules.content.load('traits')        # the parsed table, read once per process
    rules.content.path('monsters')      # its file
    rules.content.folder / 'generators' # the folder itself, for tables kept as a set of files

A table is named in the system's `tables` ({'traits': 'traits.json'}); an unnamed one is looked up as
'<name>.json'. Plain Python, like the rest of the engine.
"""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=64)
def _text(path, mtime):
    with open(path, encoding='utf-8') as file:
        return file.read()


class Content:
    def __init__(self, folder, tables):
        self.folder = Path(folder) if folder else None
        self.tables = tables or {}

    def path(self, name):
        """The file of the table with this name. KeyError for a system without content."""
        if self.folder is None:
            raise KeyError(name)
        return self.folder / self.tables.get(name, f'{name}.json')

    def has(self, name):
        return self.folder is not None and self.path(name).is_file()

    def load(self, name):
        """The table, parsed: a fresh copy each call, so a caller may change it. The file's text is cached per
        modification time, so an edited file is read again."""
        path = self.path(name)
        return json.loads(_text(str(path), path.stat().st_mtime_ns))
