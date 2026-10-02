import re
from html import unescape

from app.models import db, ContentEntry, PartyPresentation
from tests.unit.test_campaigns import setup, create_entry, login, reveal


def prepare(client, ids, campaign_id=1):
    return client.post('/materials/bulk-reveal', data={'campaign_id':campaign_id,
        'entry_ids':[str(item) for item in ids], **{f'version_{item}':'1' for item in ids}})


def confirmation(response):
    return unescape(re.search(r'name="reveal_token" value="([^"]+)"', response.get_data(as_text=True))[1])


def test_bulk_reveal_publishes_exact_selection_to_selected_audience(setup):
    app, client = setup
    parent = create_entry(client, title='Parent', body='Parent facts')
    child = create_entry(client, title='Child', parent_id=parent)
    other = create_entry(client, title='Other', body='Other facts')
    assert reveal(client, parent, title='Old text', body='Old facts').status_code == 302
    preview = prepare(client, [parent, other])
    assert preview.status_code == 200
    with app.app_context():
        assert PartyPresentation.query.count() == 1
    response = client.post('/materials/bulk-reveal', data={'reveal_token':confirmation(preview), 'party_ids':'1'})
    assert response.status_code == 302
    with app.app_context():
        rows = PartyPresentation.query.all()
        assert {row.entry_id for row in rows} == {parent, other}
        assert {row.party_id for row in rows} == {1}
        assert next(row.body for row in rows if row.entry_id == parent) == 'Parent facts'
        assert db.session.get(ContentEntry, child).presentations == []


def test_bulk_reveal_rejects_stale_or_cross_owner_selection(setup):
    app, client = setup
    first = create_entry(client, title='First')
    second = create_entry(client, title='Second')
    token = confirmation(prepare(client, [first, second]))
    with app.app_context():
        db.session.get(ContentEntry, second).body = 'Changed'
        db.session.commit()
    assert client.post('/materials/bulk-reveal',data={'reveal_token':token,'party_ids':'1'}).status_code == 409
    with app.app_context():
        assert PartyPresentation.query.count() == 0
    login(client, 4)
    assert client.post('/materials/bulk-reveal',data={'reveal_token':token,'party_ids':'3'}).status_code == 403
    login(client, 1)
    assert prepare(client, [first], campaign_id='').status_code == 400
    token = confirmation(prepare(client, [first]))
    assert client.post('/materials/bulk-reveal',data={'reveal_token':token,'party_ids':'3'}).status_code == 403
    assert client.post('/materials/bulk-reveal',data={'reveal_token':token}).status_code == 400
