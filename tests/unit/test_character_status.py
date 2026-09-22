from flask import g, render_template
from app.models import Character, User, db


def test_death_mark_is_reversible_and_owner_only(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='owner'), User(id=2, username='other')])
        character = Character(owner=1, name='Hero', url_name='hero', background='Test', items='[]')
        db.session.add(character)
        db.session.commit()
        client = app_with_babel.test_client()
        path = '/charedit/owner/hero/save'
        assert client.post(path, data={'dead': 'y'}).status_code == 302
        for user_id, expected in [(2, 403), (1, 200)]:
            g.pop('_login_user', None)
            with client.session_transaction() as session:
                session['_user_id'] = str(user_id)
            result = client.post(path, data={'name': 'Hero', 'dead': 'y', 'party_code': ''})
            assert result.status_code == expected
            assert character.dead is (user_id == 1)
        with app_with_babel.test_request_context():
            assert 'fa-skull' in render_template('partial/dead_badge.html', character=character)
        client.post(path, data={'name': 'Hero', 'party_code': ''})
        assert character.dead is False
        with app_with_babel.test_request_context():
            assert 'fa-skull' not in render_template('partial/dead_badge.html', character=character)
