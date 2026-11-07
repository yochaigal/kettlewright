import re

from flask import render_template_string
from flask_babel import force_locale


def test_party_member_card_translates_background(app_with_babel):
    # #given: the member card markup used on the party page.
    source = open('app/templates/partial/partyview/members.html', encoding='utf-8').read()
    line = re.search(r'<p class="party-member-background">.*?</p>', source).group(0)
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when
        html = render_template_string(line, character={'background': 'Fieldwarden'})
    # #then
    assert html == '<p class="party-member-background">Campero</p>'


def test_party_member_card_keeps_custom_background(app_with_babel):
    # #given: a custom background has no catalog entry.
    source = open('app/templates/partial/partyview/members.html', encoding='utf-8').read()
    line = re.search(r'<p class="party-member-background">.*?</p>', source).group(0)
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when
        html = render_template_string(line, character={'background': 'Tejedora de sueños'})
    # #then
    assert html == '<p class="party-member-background">Tejedora de sueños</p>'
