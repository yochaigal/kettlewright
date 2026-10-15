import html
import json
import re

import pytest

from app.lib.char_utils import generate_character, load_backgrounds
from app.models import Character, Companion, User


def exported(page):
    return json.loads(html.unescape(re.search(r'id="json_data" value="([^"]*)"', page)[1]))


def test_every_background_renders_an_unsaved_read_only_sheet(app_with_babel):
    with app_with_babel.test_client() as client:
        for background in load_backgrounds():
            response = client.get('/gen/character', query_string={'background':background, 'view':'sheet'})
            assert response.status_code == 200, background
            page = response.text
            snapshot = exported(page)
            assert snapshot['image_url'].startswith('humanoid/')
            assert f'images/portraits/{snapshot["image_url"]}' in page
            assert 'tools-character-preview' in page
            assert 'character-stat-dashboard' in page
            assert 'inventory-slots' in page
            assert 'background-table-answers' in page
            assert html.escape(snapshot['name']) in page
            assert 'hx-post=' not in page
            assert 'hx-get=' not in page
            assert 'data-stats-url=' not in page
            assert 'character-inline-trigger' not in page
            assert 'data-move-item=' not in page
            assert '/companions/None' not in page
            assert 'character-party-container' not in page
            assert 'character-sheet-actions-container' not in page
    with app_with_babel.app_context():
        assert Character.query.count() == Companion.query.count() == 0


def test_preview_inventory_and_export_share_the_exact_generated_snapshot(app_with_babel, monkeypatch):
    with app_with_babel.test_request_context('/'):
        generated, raw = generate_character('Outrider')
    snapshot = json.loads(raw)
    snapshot['containers'].append({'id':9, 'name':'Preview pack', 'slots':6})
    snapshot['items'][0]['location'] = 9
    raw = json.dumps(snapshot)
    from importlib import import_module
    generator_module = import_module('app.blueprints.generator')
    monkeypatch.setattr(generator_module, 'generate_character', lambda background:(generated, raw))
    page = app_with_babel.test_client().get('/gen/character?view=sheet').text
    shown = exported(page)
    assert shown['image_url'].startswith('humanoid/')
    snapshot['image_url'] = shown['image_url']
    assert shown == snapshot
    assert 'data-pcgen-inventory="9"' in page
    assert 'data-preview-container="9"' in page
    assert 'Preview pack' in page
    assert 'companion-stat-form' not in page
    assert snapshot['pets'][0]['name'] in html.unescape(page)


def test_existing_json_and_text_generator_outputs_stay_available(app_with_babel):
    client = app_with_babel.test_client()
    assert client.get('/gen/character?output=json&background=Cutpurse').json['hp'] > 0
    page = client.get('/gen/character?background=Cutpurse').text
    assert 'json_data' in page
    assert 'tools-character-preview' not in page


def test_authenticated_generator_preview_has_no_edit_actions(app_with_babel):
    from app.models import db
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='preview-owner'))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    page = client.get('/gen/character?view=sheet&background=Outrider').text
    assert 'data-generated-preview="true"' in page
    assert 'hx-post=' not in page and 'hx-get=' not in page
    assert 'companion-stat-form' not in page
    assert 'data-stats-url=' not in page
    with app_with_babel.app_context():
        assert Character.query.count() == Companion.query.count() == 0
