"""Deleting a monster from the × on its card in the party's Monsters tab."""
import pytest

from app.models import Companion, Party, User, db



@pytest.fixture
def lair(app_with_babel):
    """Party 1 (Warden 1) with three monsters and a hireling; party 2 has its own monster."""
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=1, username='warden'), User(id=2, username='player'), User(id=3, username='other')])
        db.session.add_all([
            Party(id=1, owner=1, owner_username='warden', name='Marches', party_url='marches', members='[]',
                  items='[]', containers='[{"id":0,"name":"Main","slots":10}]'),
            Party(id=2, owner=3, owner_username='other', name='Elsewhere', party_url='elsewhere', members='[]',
                  items='[]', containers='[{"id":0,"name":"Main","slots":10}]'),
        ])
        for cid, party_id, kind, name in [(1, 1, 'monster', 'Goblin'), (2, 1, 'monster', 'Wolf'),
                                          (3, 1, 'monster', '<img src=x onerror=alert(1)>'),
                                          (4, 1, 'hireling', 'Torchbearer'), (5, 2, 'monster', 'Their troll')]:
            db.session.add(Companion(id=cid, kind=kind, party_id=party_id, name=name, hp=3, hp_max=3,
                                     strength=10, strength_max=10, dexterity=10, dexterity_max=10,
                                     willpower=10, willpower_max=10, shared=kind == 'hireling'))
        db.session.commit()
    return app


def client_for(app, user_id):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
    return client


def remaining(app):
    with app.app_context():
        return {c.id for c in Companion.query.all()}


def test_the_cross_deletes_one_monster_and_returns_to_the_tab(lair):
    response = client_for(lair, 1).post('/companions/2/delete')
    assert response.status_code == 302 and response.location.endswith('/users/warden/parties/marches/#monsters')
    assert remaining(lair) == {1, 3, 4, 5}


@pytest.mark.parametrize('user, companion', [(2, 1), (3, 1), (1, 5)])
def test_only_the_warden_deletes_their_own_monsters(lair, user, companion):
    assert client_for(lair, user).post(f'/companions/{companion}/delete').status_code == 403
    assert remaining(lair) == {1, 2, 3, 4, 5}


def test_each_monster_card_has_a_cross(lair):
    page = client_for(lair, 1).get('/users/warden/parties/marches/').get_data(as_text=True)
    tab = page[page.index('id="monsters"'):]
    for monster in (1, 2, 3):
        assert f'action="/companions/{monster}/delete" data-confirm-delete' in tab
    assert tab.count('class="companion-delete"') == 3
    assert 'companion_ids' not in page and 'monster-bulk-form' not in page  # No multi-selection.
    # Names are escaped in the confirmation text (the script escapes again before display).
    assert '<img src=x' not in tab and '&lt;img src=x onerror=alert(1)&gt;' in tab
    # Hireling cards elsewhere on the page get no ×.
    assert '/companions/4/delete' not in page


def test_players_get_no_cross(lair):
    text = client_for(lair, 2).get('/users/warden/parties/marches/').get_data(as_text=True)
    assert 'companion-delete' not in text
