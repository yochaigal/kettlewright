import pytest
import tempfile
import os
import sys

# Set required environment variables before importing Flask app
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
os.environ.setdefault('USE_REDIS', 'False')

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    from app import create_app
    
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
        "USE_REDIS": False,
    })

    # Create the database and the database table(s)
    with app.app_context():
        db.create_all()

    yield app

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def app_with_babel(app):
    """App fixture with Babel initialized for tests that need translation."""
    from flask_babel import Babel
    babel = Babel(app, locale_selector=lambda: 'en')
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