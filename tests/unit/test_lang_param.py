"""A ?lang= link keeps its language on the follow-up requests the page makes."""
import pytest
from flask_babel import Babel

from app import get_locale


@pytest.fixture
def client(app):
    Babel(app, locale_selector=get_locale)
    return app.test_client()


def test_lang_param_carries_over_to_requests_without_it(client):
    # #given a visitor opens a shared link with ?lang=ru
    client.get('/about?lang=ru')
    # #when the next request carries no lang parameter
    page = client.get('/about').get_data(as_text=True)
    # #then it is still Russian
    assert '>вики</a>' in page


def test_unsupported_lang_param_falls_back_to_english(client):
    # #given a link with a language the app does not ship
    # #when the page is requested
    response = client.get('/about?lang=xx')
    # #then it renders in English instead of failing
    assert (response.status_code, '>wiki</a>' in response.get_data(as_text=True)) == (200, True)


def test_unsupported_lang_param_is_not_remembered(client):
    # #given a link with a language the app does not ship
    response = client.get('/about?lang=xx')
    # #when the response is sent
    cookies = response.headers.getlist('Set-Cookie')
    # #then no language cookie is set
    assert [c for c in cookies if c.startswith('kw_lang=')] == []
