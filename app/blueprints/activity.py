"""The party whiteboard as a Discord Activity (#423). See app/lib/activity.py and docs/discord.md."""
import os
from urllib.parse import quote

import requests
from flask import (Blueprint, abort, current_app, g, jsonify, make_response, redirect, render_template,
                   request, send_from_directory, url_for)
from flask_babel import _
from flask_login import login_required
from werkzeug.routing import PathConverter

from app.lib import activity as tokens
from app.models import DiscordAccount

activity = Blueprint('activity', __name__)
API = 'https://discord.com/api/v10'


class EsmPath(PathConverter):
    """Only esm.sh module paths ("name@1.2.3/…", "name@^1.2", "@scope/name@1.2.3/…", Node polyfills "node/process.mjs").
    No site URL looks like this: usernames cannot contain "@", and nothing else lives under /node/."""
    regex = r'(?:(?:@[A-Za-z0-9][\w.-]*/)?[A-Za-z0-9][\w.-]*@[^/]+(?:/.*)?|node/[\w.-]+\.mjs)'


# Registered before the routes below are added.
activity.record_once(lambda state: state.app.url_map.converters.setdefault('esm', EsmPath))


def _no_store(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


def _refuse(reason, message, status=403, link=None):
    return _no_store(make_response(jsonify(reason=reason, message=message, link=link), status))


@activity.get('/activity')
def launch():
    """Discord opens the Activity at "/"; main.index sends its launch parameters here."""
    from app.blueprints.discord import enabled
    if not enabled():
        abort(404)
    return _no_store(make_response(render_template('activity/launch.html',
        client_id=current_app.config['DISCORD_APPLICATION_ID'])))


@activity.post('/activity/token')
def token():
    """Exchange the SDK's authorization code for a ticket to the board of the channel's party.

    No CSRF token: the request carries a single-use code that only Discord can issue for this app.
    """
    from app.blueprints.discord import enabled, snowflake
    from app.lib.discord_commands import linked_party, site_url
    from app.socket_events import party_recipient_ids
    if not enabled():
        abort(404)
    data = request.get_json(silent=True) or {}
    code, guild_id, channel_id = data.get('code'), data.get('guild_id'), data.get('channel_id')
    if not isinstance(code, str) or not 0 < len(code) <= 200 or not snowflake(channel_id) or not snowflake(guild_id):
        return _refuse('invalid', _('Open the whiteboard from a Discord server channel.'), 400)
    try:
        response = requests.post(API + '/oauth2/token', data=dict(
            client_id=current_app.config['DISCORD_APPLICATION_ID'],
            client_secret=current_app.config['DISCORD_CLIENT_SECRET'],
            grant_type='authorization_code', code=code), timeout=5)
        response.raise_for_status()
        access = response.json()['access_token']
        response = requests.get(API + '/users/@me', headers={'Authorization': 'Bearer ' + access}, timeout=5)
        response.raise_for_status()
        discord_id = response.json()['id']
    except (requests.RequestException, ValueError, KeyError, TypeError):
        # Never log Discord's responses: they hold codes and tokens.
        return _refuse('discord', _('Discord did not confirm who you are. Close the whiteboard and open it again.'), 502)
    account = DiscordAccount.query.filter_by(discord_id=str(discord_id)).first()
    if account is None:
        return _refuse('not_linked', _('Connect your Discord account to Kettlewright first, then open the whiteboard again.'),
                       link=site_url(url_for('discord.settings')))
    try:
        party = linked_party(guild_id, channel_id)[1]
    except ValueError:
        return _refuse('not_bound', _('This channel has no party yet. The Warden can bind one with /kw bind.'))
    if account.user_id not in party_recipient_ids(party):
        return _refuse('not_member', _('Only members of %(party)s can open its whiteboard.', party=party.name))
    ticket = tokens.issue('ticket', account.user_id, party.id, account.discord_id)
    return _no_store(jsonify(board=url_for('activity.board', party_id=party.id, ticket=ticket), party=party.name))


@activity.get('/activity/board/<int:party_id>')
@login_required
def board(party_id):
    """The whiteboard page inside Discord, opened with a ticket (app.lib.activity.load_request_user)."""
    from app.blueprints.party import shared_map_page
    claims = g.get('activity')
    if not claims or claims['p'] != party_id:
        abort(403)
    session_token = tokens.issue('session', claims['u'], claims['p'], claims['d'], claims['c'])
    response = shared_map_page(party_id, activity_token=session_token)
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@activity.get('/activity/static/<path:filename>')
def static(filename):
    """Static files for the Activity. Whiteboard modules have their bare imports rewritten."""
    if filename.startswith('src/js/') and filename.endswith('.js'):
        path = os.path.join(current_app.static_folder, filename)
        if not os.path.realpath(path).startswith(os.path.realpath(current_app.static_folder) + os.sep) or not os.path.isfile(path):
            abort(404)
        with open(path, encoding='utf-8') as file:
            response = make_response(tokens.rewrite_imports(file.read()))
        response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
        response.headers['Cache-Control'] = 'no-cache'
        return response
    return send_from_directory(current_app.static_folder, filename)


@activity.get('/<esm:path>')
def esm_redirect(path):
    """Send an esm.sh module path to Discord's /esm mapping. These paths are versioned, so it is cached."""
    if not tokens.ESM_PATH.match(path):
        abort(404)
    target = '/esm/' + quote(path, safe='/@.,=-_~+')
    if request.query_string:
        target += '?' + request.query_string.decode('latin-1')
    response = redirect(target, 301)
    response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response
