from io import BytesIO

import pytest
from PIL import Image
from flask import g

from app.models import Character, User, db


@pytest.fixture
def portrait_client(app_with_babel, tmp_path):
    app_with_babel.config['PORTRAIT_UPLOAD_FOLDER'] = str(tmp_path)
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='owner'), User(id=2, username='other')])
        db.session.add(Character(id=1, name='Hero', url_name='hero', owner=1,
                                 background='Test', image_url='original.webp', custom_image=False))
        db.session.commit()
        client = app_with_babel.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = '1'
        yield client, tmp_path


def png(size=(600, 400)):
    data = BytesIO()
    Image.new('RGB', size, 'red').save(data, 'PNG')
    data.seek(0)
    return data


PATH = '/charedit/inplace-portrait/owner/hero/save'


def test_upload_is_normalized_and_served_with_safe_type(portrait_client):
    client, folder = portrait_client
    response = client.post(PATH, data={'portrait-file': (png(), '../../portrait.html')})
    assert response.status_code == 200
    assert 'HX-Redirect' in response.headers
    character = db.session.get(Character, 1)
    assert character.custom_image is True
    response = client.get(character.image_url)
    assert response.mimetype == 'image/webp'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    with Image.open(BytesIO(response.data)) as image:
        assert image.size == (256, 256)
    assert len(list(folder.iterdir())) == 1


@pytest.mark.parametrize('raw', [b'<svg onload="alert(1)"></svg>', b'broken', b'x' * (2 * 1024 * 1024 + 1), b'x' * (3 * 1024 * 1024 + 1)],
                         ids=['svg', 'corrupt', 'file-too-large', 'request-too-large'])
def test_invalid_file_does_not_replace_portrait(portrait_client, raw):
    client, folder = portrait_client
    response = client.post(PATH, data={'portrait-file': (BytesIO(raw), 'portrait.png')})
    assert 'role="alert"' in response.get_data(as_text=True)
    assert db.session.get(Character, 1).image_url == 'original.webp'
    assert not list(folder.iterdir())


def test_large_dimensions_are_rejected(portrait_client):
    client, _ = portrait_client
    response = client.post(PATH, data={'portrait-file': (png((4097, 1)), 'wide.png')})
    assert '4096' in response.get_data(as_text=True)
    assert db.session.get(Character, 1).image_url == 'original.webp'


def test_nonowner_upload_and_csrf_are_rejected(portrait_client):
    client, folder = portrait_client
    with client.session_transaction() as session:
        session['_user_id'] = '2'
    assert client.post(PATH, data={'portrait-file': (png(), 'image.png')}).status_code == 403
    g.pop('_login_user', None)
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    client.application.config['WTF_CSRF_ENABLED'] = True
    assert client.post(PATH, data={'portrait-file': (png(), 'image.png')}).status_code == 400
    assert not list(folder.iterdir())
