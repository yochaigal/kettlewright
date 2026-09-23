import re
from unittest.mock import patch

import pytest
from app.models import db, User, MFAChallenge


@pytest.fixture
def mfa(app_with_babel):
    app = app_with_babel
    with app.app_context():
        user = User(id=1, username='mfa', email='mfa@example.com', confirmed=True, mfa_enabled=True)
        user.password = 'password123'
        db.session.add(user)
        db.session.commit()
    with patch('app.email.send_email') as send:
        yield app, app.test_client(), send


def login(client, **extra):
    return client.post('/login?next=/account', data=dict(email='mfa@example.com', password='password123', **extra))


def code(send):
    return send.call_args.kwargs['code']


def test_password_alone_cannot_login_and_code_is_single_use(mfa):
    app, client, send = mfa
    assert login(client, remember_me='y').location.endswith('/mfa/verify')
    with client.session_transaction() as session:
        assert '_user_id' not in session
        pending = dict(session['mfa_pending'])
        assert code(send) not in str(session)
    assert client.get('/account').status_code == 302
    assert client.get('/mfa/verify').status_code == 200
    assert client.post('/mfa/verify', data={'code':code(send)}).location.endswith('/account')
    with client.session_transaction() as session:
        assert session['_user_id'] == '1'
    with app.app_context():
        assert MFAChallenge.query.count() == 0
    replay = app.test_client()
    with replay.session_transaction() as session:
        session['mfa_pending'] = pending
    replay.post('/mfa/verify', data={'code':code(send)})
    with replay.session_transaction() as session:
        assert '_user_id' not in session


def test_attempt_limit_survives_cookie_replay(mfa):
    app, client, send = mfa
    login(client)
    with client.session_transaction() as session:
        pending = dict(session['mfa_pending'])
    bad = '999999' if code(send) != '999999' else '000000'
    for _ in range(5):
        client.post('/mfa/verify', data={'code':bad})
    with client.session_transaction() as session:
        session['mfa_pending'] = pending
    client.post('/mfa/verify', data={'code':code(send)})
    with client.session_transaction() as session:
        assert '_user_id' not in session


@pytest.mark.parametrize('change', ['expires', 'password', 'email'])
def test_expiration_and_credentials_invalidate_code(mfa, change):
    app, client, send = mfa
    login(client)
    with app.app_context():
        if change == 'expires': MFAChallenge.query.one().expires = 0
        elif change == 'password': db.session.get(User,1).password = 'changed123'
        else: db.session.get(User,1).email = 'changed@example.com'
        db.session.commit()
    with app.app_context():
        from app.lib.mfa import pending_challenge
        assert pending_challenge(MFAChallenge.query.one().nonce) is None
    client.post('/mfa/verify', data={'code':code(send)})
    with client.session_transaction() as session:
        assert '_user_id' not in session


def test_resend_cooldown_and_old_code_revoked(mfa):
    app, client, send = mfa
    login(client)
    first = code(send)
    client.post('/mfa/resend')
    assert send.call_count == 1
    with app.app_context():
        MFAChallenge.query.one().sent_at -= 61
        db.session.commit()
    client.post('/mfa/resend')
    assert send.call_count == 2
    if first != code(send):
        client.post('/mfa/verify', data={'code':first})
        with client.session_transaction() as session: assert '_user_id' not in session
    assert client.post('/mfa/verify', data={'code':code(send)}).location.endswith('/account')


def test_settings_require_password_and_email_for_enable_and_disable(mfa):
    app, client, send = mfa
    with app.app_context():
        db.session.get(User,1).mfa_enabled = False
        db.session.commit()
    assert login(client).location.endswith('/account')
    client.post('/account/mfa', data={'password':'wrong'})
    assert not send.called
    for enabled in (True, False):
        assert client.post('/account/mfa', data={'password':'password123'}).location.endswith('/mfa/verify')
        with app.app_context(): assert db.session.get(User,1).mfa_enabled is not enabled
        client.post('/mfa/verify', data={'code':code(send)})
        with app.app_context(): assert db.session.get(User,1).mfa_enabled is enabled


def test_delivery_failure_never_logs_in(mfa):
    app, client, send = mfa
    send.side_effect = RuntimeError('smtp down')
    assert login(client).status_code == 503
    with client.session_transaction() as session: assert '_user_id' not in session
    with app.app_context(): assert MFAChallenge.query.count() == 0


def test_mfa_prevents_changing_email_without_code(mfa):
    app, client, send = mfa
    with client.session_transaction() as session: session['_user_id'] = '1'
    assert client.post('/change_email', data={'password':'password123', 'email':'changed@example.com', 'email2':'changed@example.com'}).location.endswith('/account/mfa')
    with app.app_context(): assert db.session.get(User,1).email == 'mfa@example.com'


def test_csrf_and_safe_redirect(mfa):
    app, client, send = mfa
    app.config['WTF_CSRF_ENABLED'] = True
    login(client)
    assert not send.called
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', client.get('/login').text).group(1)
    client.post('/login?next=//evil.example', data={'email':'mfa@example.com','password':'password123','csrf_token':token})
    client.post('/mfa/verify', data={'code':code(send)})
    with client.session_transaction() as session: assert '_user_id' not in session
    assert client.post('/mfa/resend').status_code == 400
    response = client.post('/mfa/verify', data={'code':code(send),'csrf_token':token})
    assert response.location == '/users/mfa/characters/'


def test_remembered_session_must_reauthenticate_before_settings(mfa):
    app, client, send = mfa
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = False
    response = client.get('/account/mfa')
    assert '/reauthenticate' in response.location
    client.post('/reauthenticate', data={'password':'wrong'})
    with client.session_transaction() as session: assert session['_fresh'] is False
    assert client.post('/reauthenticate', data={'password':'password123'}).location.endswith('/account/mfa')
    assert client.get('/account/mfa').status_code == 200
    assert not send.called


def test_smtp_debug_logging_is_disabled(mfa):
    app,_,_ = mfa
    assert app.extensions['mail'].debug == 0
