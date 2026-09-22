import json

from app.models import Character, User, db


def test_print_omits_empty_sections_but_preserves_long_notes_and_stored_items(app_with_babel):
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='printer'))
        character = Character(owner=1, name='Print Hero', url_name='hero', background='Test',
                              image_url='default-portrait.webp', custom_image=False,
                              bonds='', description='', omens='', notes='A long record. ' * 1000,
                              items=json.dumps([dict(id='book', name='Stored book', tags=[], location=2)]),
                              containers=json.dumps([dict(id=0, name='Main', slots=10),
                                                     dict(id=1, name='Empty chest', slots=20),
                                                     dict(id=2, name='Occupied chest', slots=20)]))
        db.session.add(character)
        db.session.commit()
    response = app_with_babel.test_client().get('/users/printer/characters/hero/print/')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'Empty chest' not in page
    assert 'Occupied chest' in page and 'Stored book' in page
    assert 'character-print-bonds-container' not in page
    assert 'character-print-description-container' not in page
    assert 'character-no-party-description' not in page
    assert page.count('A long record.') == 1000
