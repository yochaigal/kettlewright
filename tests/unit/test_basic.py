"""Basic smoke tests to verify the test setup works."""
import pytest


def test_app_creation(app):
    """Test that the Flask app can be created."""
    assert app is not None
    assert app.config['TESTING'] is True


def test_app_context(app_context):
    """Test that app context is working."""
    from flask import current_app
    assert current_app is not None


def test_client_access(client):
    """Test that test client can access a simple endpoint."""
    response = client.get('/')
    # Home page redirects to login when not authenticated
    assert response.status_code == 302