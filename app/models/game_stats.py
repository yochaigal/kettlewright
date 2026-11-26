"""Stats from the game system (kettlewright, #487) on a character or companion sheet.

A stat with a column of its own (all of Cairn's: hp, strength, ... and their *_max) is read and written there.
Any other stat a system adds is kept in the sheet's system_stats JSON, so a second system does not need new
columns. The model mixing this in has a system_stats Text column.
"""
from kettlewright import system
import json


class SystemStats:
    def _extra_stat_name(self, name):
        """Whether name is a stat (or its _max) or condition of the game system without a column of its own."""
        if name.startswith('_') or hasattr(type(self), name):
            return False
        try:
            rules = system()
        except Exception:
            return False
        return name.removesuffix('_max') in rules.stat_keys or name in rules.condition_keys

    def __setattr__(self, name, value):
        """character.luck = 5 is kept in system_stats, like a column would keep it."""
        if self._extra_stat_name(name):
            self.set_stat(name, value)
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        """character.luck, character['luck'] in a template: a stat (or its _max, or a condition) of the game system
        that has no column reads from system_stats. Only for names that aren't attributes already."""
        if name.startswith('_') or name == 'system_stats':
            raise AttributeError(name)
        try:
            rules = system()
        except Exception:
            raise AttributeError(name) from None
        base = name.removesuffix('_max')
        if base in rules.stat_keys or name in rules.condition_keys:
            return self._extra_stats().get(name)
        raise AttributeError(name)

    def _extra_stats(self):
        try:
            data = json.loads(self.system_stats or '{}')
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def has_column(self, field):
        return field in self.__table__.columns

    def get_stat(self, field, default=None):
        """A stat's value by its field ('strength', 'strength_max', 'luck'...)."""
        if self.has_column(field):
            value = getattr(self, field)
            return default if value is None else value
        return self._extra_stats().get(field, default)

    def set_stat(self, field, value):
        if self.has_column(field):
            setattr(self, field, value)
            return
        data = self._extra_stats()
        data[field] = value
        super().__setattr__('system_stats', json.dumps(data, sort_keys=True))

    def stat_values(self):
        """{field: [current, maximum]} for each of the system's stats, HP first."""
        return {stat.key: [self.get_stat(stat.key), self.get_stat(stat.key + '_max')] for stat in system().stats}
