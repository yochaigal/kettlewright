"""Cairn, second edition (cairnrpg.com): the system Kettlewright was built for. Registered with the engine on import."""
from kettlewright.registry import register

from systems.cairn.system import CAIRN, Cairn

register(CAIRN)

__all__ = ['CAIRN', 'Cairn']
