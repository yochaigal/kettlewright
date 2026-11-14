"""Dice rolled inside htmx partials or before redirects reach the browser as 3D dice."""
import json

from flask import Flask, redirect, render_template_string

from app.lib.dice_feedback import pending_dice, queue_dice, send_queued_dice


def make_app():
    app = Flask(__name__)
    app.secret_key = 'test'
    app.after_request(lambda response: send_queued_dice(response, __import__('flask').request))

    @app.post('/partial')
    def partial():
        queue_dice([2, 5, 6], 6)
        return 'partial'

    @app.post('/partial-with-trigger')
    def partial_with_trigger():
        queue_dice([4], [20])
        return 'partial', 200, {'HX-Trigger': 'omen-roll'}

    @app.post('/redirect')
    def go():
        queue_dice([3], [6])
        return redirect('/page')

    @app.get('/page')
    def page():
        return render_template_string('{{ dice|tojson }}', dice=pending_dice())

    @app.post('/nothing')
    def nothing():
        return 'ok'
    return app


def test_htmx_partial_gets_dice_trigger():
    client = make_app().test_client()
    response = client.post('/partial', headers={'HX-Request': 'true'})
    assert json.loads(response.headers['HX-Trigger']) == {'dice3d': {'values': [2, 5, 6], 'sides': [6, 6, 6]}}


def test_existing_trigger_is_kept():
    client = make_app().test_client()
    response = client.post('/partial-with-trigger', headers={'HX-Request': 'true'})
    assert json.loads(response.headers['HX-Trigger']) == {'omen-roll': None, 'dice3d': {'values': [4], 'sides': [20]}}


def test_redirect_shows_dice_once_on_next_page():
    client = make_app().test_client()
    response = client.post('/redirect')
    assert response.status_code == 302 and 'HX-Trigger' not in response.headers
    assert json.loads(client.get('/page').data) == {'values': [3], 'sides': [6]}
    assert json.loads(client.get('/page').data) is None


def test_no_roll_no_header():
    client = make_app().test_client()
    assert 'HX-Trigger' not in client.post('/nothing', headers={'HX-Request': 'true'}).headers


def test_queue_is_capped_and_ignores_mismatched_input():
    app = make_app()
    with app.test_request_context():
        from flask import g
        queue_dice([1, 2], [6])
        assert 'dice3d' not in g
        queue_dice([1] * 20, 6)
        assert len(g.dice3d['values']) == 12
