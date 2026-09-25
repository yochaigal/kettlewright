"""Production entry point: patch networking before loading the preloaded app."""
from gevent import monkey

monkey.patch_all()

from app import application  # noqa: E402
