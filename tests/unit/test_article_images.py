"""An article's own image (#476): uploaded apart from its text, shown above it and on its card."""
import base64
import io
import json
import zipfile

from PIL import Image

from app.models import db, ContentEntry
from tests.helpers import login
from tests.unit.test_campaigns import setup, create_entry, reveal, module_url  # noqa: F401 (fixture)


def png(color='red', size=(6, 4)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()


def stored_image(app, entry_id):
    with app.app_context():
        return db.session.get(ContentEntry, entry_id).image


def edit(client, entry_id, version, **values):
    return client.post(f'/materials/{entry_id}/edit', data={'version': version, 'title': 'SECRET NAME',
        'body': 'SECRET BODY', 'category': 'npc', 'campaign_id': 1, **values})


def test_upload_is_stored_and_shown_above_the_text(setup):
    app, client = setup
    entry_id = create_entry(client, image=png())
    image = stored_image(app, entry_id)
    assert image.startswith('/material-images/1/') and image.endswith('.webp')
    with app.app_context():
        assert 'material-images' not in db.session.get(ContentEntry, entry_id).body
    page = client.get(f'/campaigns/1/wiki/{entry_id}/').get_data(as_text=True)
    assert f'src="/materials/{entry_id}/image"' in page and 'class="wiki-image"' in page
    picture = client.get(f'/materials/{entry_id}/image')
    assert picture.status_code == 200 and picture.mimetype == 'image/webp'
    # The editor shows it, ready to change or remove.
    assert f'data-value="{image}"' in client.get(f'/materials/{entry_id}/edit').get_data(as_text=True)


def test_editing_keeps_changes_or_removes_the_image(setup, tmp_path):
    app, client = setup
    entry_id = create_entry(client, image=png())
    first = stored_image(app, entry_id)
    assert edit(client, entry_id, 1, image=first).status_code == 302  # Unchanged.
    assert stored_image(app, entry_id) == first
    assert edit(client, entry_id, 2).status_code == 302  # A form without the field keeps it.
    assert stored_image(app, entry_id) == first
    assert edit(client, entry_id, 3, image=png('blue')).status_code == 302
    second = stored_image(app, entry_id)
    assert second != first
    folder = tmp_path / 'material-images' / '1'
    assert not (folder / first.rsplit('/', 1)[1]).exists()  # The replaced picture is cleaned up.
    assert edit(client, entry_id, 4, image='').status_code == 302
    assert stored_image(app, entry_id) == ''
    assert not (folder / second.rsplit('/', 1)[1]).exists()
    assert client.get(f'/materials/{entry_id}/image').status_code == 404


def test_invalid_or_foreign_images_are_refused(setup):
    app, client = setup
    entry_id = create_entry(client)
    assert edit(client, entry_id, 1, image='data:image/png;base64,bm90YW5pbWFnZQ==').status_code == 400
    assert edit(client, entry_id, 1, image='javascript:alert(1)').status_code == 400
    assert edit(client, entry_id, 1, image='/material-images/4/' + 'a' * 32 + '.webp').status_code == 400
    assert edit(client, entry_id, 1, image='https://example.com/castle.png').status_code == 302
    assert stored_image(app, entry_id) == 'https://example.com/castle.png'


def test_party_sees_the_image_only_once_revealed(setup):
    app, client = setup
    entry_id = create_entry(client, image=png())
    login(client, 2)
    assert client.get(f'/party/1/materials/{entry_id}/image').status_code == 404
    login(client, 1)
    assert reveal(client, entry_id).status_code == 302
    login(client, 2)
    picture = client.get(f'/party/1/materials/{entry_id}/image')
    assert picture.status_code == 200 and picture.mimetype == 'image/webp'
    page = client.get(f'/party/1/materials/{entry_id}').get_data(as_text=True)
    assert f'src="/party/1/materials/{entry_id}/image"' in page
    # The stored file itself stays private: it is not in any text.
    assert client.get(stored_image(app, entry_id)).status_code == 404


def test_card_prefers_its_own_image(setup):
    app, client = setup
    from app.lib.rich_content import RICH_PREFIX
    entry_id = create_entry(client, body=RICH_PREFIX + '<p><img src="https://example.com/in-text.png"></p>',
                           image='https://example.com/own.png')
    assert client.get(f'/materials/{entry_id}/image').location == 'https://example.com/own.png'
    assert edit(client, entry_id, 1, image='', body=RICH_PREFIX + '<p><img src="https://example.com/in-text.png"></p>').status_code == 302
    assert client.get(f'/materials/{entry_id}/image').location == 'https://example.com/in-text.png'


def test_export_and_import_keep_an_image_url(setup):
    app, client = setup
    create_entry(client, title='Castle', image='https://example.com/castle.png')
    archive = client.get(module_url(app, suffix='export'))
    assert archive.status_code == 200
    with zipfile.ZipFile(io.BytesIO(archive.data)) as files:
        text = next(files.read(name).decode() for name in files.namelist() if name.lower().endswith('castle.md'))
    assert 'image: https://example.com/castle.png' in text
    import pytest
    from app.lib.campaign_import import ImportError as ArchiveError, parse_markdown, imported_image
    assert parse_markdown('articles/castle.md', text)['image'] == 'https://example.com/castle.png'
    with pytest.raises(ArchiveError):
        parse_markdown('articles/bad.md', text.replace('https://example.com/castle.png', 'javascript:alert(1)'))
    # Someone else's stored picture is left out of an import.
    with app.app_context():
        assert imported_image('/material-images/4/' + 'a' * 32 + '.webp', 1) == ''
        assert imported_image('https://example.com/castle.png', 1) == 'https://example.com/castle.png'


def test_campaign_cover_can_be_an_articles_image(setup):
    app, client = setup
    entry_id = create_entry(client, image=png())
    response = client.get('/campaigns/1/cover')
    assert response.status_code == 302 and response.location == stored_image(app, entry_id)
    assert client.get(response.location).status_code == 200  # Its owner sees it.
    login(client, 2)
    assert client.get(response.location).status_code == 404  # Nobody else does.
