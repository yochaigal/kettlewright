import os
import sys

import pytest

# Set required environment variables before importing Flask app
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
os.environ.setdefault('USE_REDIS', 'False')

# Add the project root to the Python path, and run from it: the app and its migrations
# use paths relative to the repository root, wherever pytest was started.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from app.models import db


def _build_app():
    """create_app() binds the database engine from SQLALCHEMY_DATABASE_URI (in-memory SQLite, set above)."""
    from app import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
        "USE_REDIS": False,
    })
    return app


def _empty_database():
    """Delete every row (much faster than dropping tables); ids restart at 1 as in a new database."""
    db.session.remove()
    with db.engine.begin() as connection:
        for table in reversed(db.metadata.sorted_tables):
            connection.execute(table.delete())
        if connection.exec_driver_sql("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").first():
            connection.exec_driver_sql('DELETE FROM sqlite_sequence')


@pytest.fixture(scope='session')
def _session_app():
    """Build the Flask app once per test session (per xdist worker).

    create_app() compiles ~230 routes and the stylesheet bundle, which used to cost
    most of the suite's run time when repeated for every test. Each test still gets
    an empty database and its own copy of the config; see `app` below.
    """
    app = _build_app()
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def app(_session_app):
    """The shared app with a fresh database, config and translation setup for this test."""
    app = _session_app
    config = dict(app.config)
    babel = app.extensions.get('babel')
    with app.app_context():
        _empty_database()

    yield app

    with app.app_context():
        db.session.remove()
    app.config.clear()
    app.config.update(config)
    if babel is None:
        app.extensions.pop('babel', None)
    else:
        app.extensions['babel'] = babel


@pytest.fixture
def fresh_app():
    """A brand-new app for the rare test that must change app setup (hooks, blueprints)."""
    app = _build_app()
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()


@pytest.fixture
def app_with_babel(app):
    """App fixture with Babel initialized for tests that need translation."""
    from flask_babel import Babel
    Babel(app, locale_selector=lambda: 'en')
    return app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Provide application context for tests."""
    with app.app_context():
        yield


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def fresh_presence():
    """Every test starts with nobody connected (#424), so socket events never depend on test order."""
    import app.lib.presence as presence
    presence._presence = presence.Presence()
    yield presence._presence
    presence._presence = None


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    """Socket and Discord limits are per process; a shared test app must not carry counts between tests."""
    from app.lib.socket_rate_limit import SocketRateLimiter
    SocketRateLimiter.reset_all()
    yield
