"""Exercise the real signup route with isolated storage and mocked Google/mail."""
import importlib
import json
from unittest.mock import Mock

import pytest
import requests
from flask import Flask
from flask_babel import Babel
from flask_login import LoginManager

from app.models import db

auth_module = importlib.import_module('app.blueprints.auth')


@pytest.fixture
def signup_app(monkeypatch):
    monkeypatch.setenv('REQUIRE_SIGNUP_CODE', 'False')
    monkeypatch.setenv('USE_CAPTCHA', 'True')
    monkeypatch.setenv('CAPTCHA_BLOCK', 'True')
    monkeypatch.setenv('CAPTCHA_PROJECT_ID', 'test-project')
    monkeypatch.setenv('CAPTCHA_KEY', 'test-site-key')
    monkeypatch.setenv('CAPTCHA_API_KEY', 'test-api-key')
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='test-secret',
                      SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
                      WTF_CSRF_ENABLED=False)
    db.init_app(app)
    Babel(app, locale_selector=lambda: 'en')
    login_manager = LoginManager(app)
    login_manager.user_loader(lambda user_id: None)
    app.register_blueprint(auth_module.auth)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def mail_mock(monkeypatch):
    send = Mock()
    monkeypatch.setattr(auth_module, 'send_email', send)
    return send


@pytest.fixture
def google_mock(monkeypatch):
    post = Mock()
    monkeypatch.setattr(auth_module.requests, 'post', post)
    return post


def assessment(score=0.9, valid=True, action='signup'):
    return {'tokenProperties': {'valid': valid, 'action': action},
            'riskAnalysis': {'score': score}}


def google_response(payload, status=200):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode()
    response._content_consumed = True
    return response


def submit(app, token='test-token'):
    return app.test_client().post('/signup', data={
        'email': 'Tester@example.com', 'user_name': 'Tester',
        'password': 'test-password', 'password2': 'test-password',
        'captcha_token': token,
    })


@pytest.mark.parametrize('score', [0.7, 0.9, 1.0])
def test_valid_low_risk_signup(signup_app, google_mock, mail_mock, score):
    google_mock.return_value = google_response(assessment(score))
    response = submit(signup_app)
    assert response.status_code == 302
    assert response.location == '/login'
    assert auth_module.User.query.one().email == 'tester@example.com'
    mail_mock.assert_called_once()
    args, kwargs = google_mock.call_args
    assert args[0].endswith('/projects/test-project/assessments?key=test-api-key')
    assert kwargs['json']['event'] == {
        'token': 'test-token', 'siteKey': 'test-site-key',
        'userIpAddress': '127.0.0.1', 'expectedAction': 'signup',
    }
    assert kwargs['timeout'] > 0


@pytest.mark.parametrize('payload', [
    assessment(0.0), assessment(0.3), assessment(0.69),
    assessment(valid=False), assessment(action='login'),
    {}, {'tokenProperties': {'valid': True, 'action': 'signup'}},
    {'tokenProperties': {'action': 'signup'}, 'riskAnalysis': {'score': 0.9}},
    assessment(score=None), assessment(score='0.9'), assessment(score=True),
    assessment(score=1.1), assessment(score=float('nan')),
    {'tokenProperties': None, 'riskAnalysis': None}, [], None,
])
def test_rejects_risky_or_invalid_assessment(signup_app, google_mock, mail_mock, payload):
    google_mock.return_value = google_response(payload)
    response = submit(signup_app)
    assert response.status_code == 302
    assert response.location == '/signup'
    assert auth_module.User.query.count() == 0
    mail_mock.assert_not_called()


@pytest.mark.parametrize('failure', ['http', 'timeout', 'json'])
@pytest.mark.parametrize('blocking', [True, False])
def test_google_failure_respects_blocking_mode(
        signup_app, google_mock, mail_mock, monkeypatch, failure, blocking):
    monkeypatch.setenv('CAPTCHA_BLOCK', str(blocking))
    if failure == 'timeout':
        google_mock.side_effect = requests.Timeout('test timeout')
    elif failure == 'http':
        google_mock.return_value = google_response({'error': {}}, status=503)
    else:
        response = google_response({})
        response._content = b'not JSON'
        google_mock.return_value = response
    response = submit(signup_app)
    assert response.status_code == 302
    assert response.location == ('/signup' if blocking else '/login')
    assert auth_module.User.query.count() == (0 if blocking else 1)
    assert mail_mock.call_count == (0 if blocking else 1)


def test_monitor_mode_allows_risky_signup(signup_app, google_mock, mail_mock, monkeypatch):
    monkeypatch.setenv('CAPTCHA_BLOCK', 'False')
    google_mock.return_value = google_response(assessment(0.1))
    assert submit(signup_app).location == '/login'
    assert auth_module.User.query.count() == 1
    mail_mock.assert_called_once()


def test_disabled_captcha_skips_google(signup_app, google_mock, mail_mock, monkeypatch):
    monkeypatch.setenv('USE_CAPTCHA', 'False')
    assert submit(signup_app, token='').location == '/login'
    google_mock.assert_not_called()
    mail_mock.assert_called_once()


def test_missing_token_is_rejected(signup_app, google_mock, mail_mock):
    assert submit(signup_app, token='').location == '/signup'
    google_mock.assert_not_called()
    assert auth_module.User.query.count() == 0
    mail_mock.assert_not_called()
