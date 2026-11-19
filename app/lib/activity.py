"""The party whiteboard as a Discord Activity (#423).

Discord shows an Activity in an iframe on <application id>.discordsays.com and forwards
requests to Kettlewright through its proxy. Cookies are unreliable there, so the Activity
signs in with the Embedded App SDK and then carries a signed token on every request:

- a *ticket* (two minutes) opens the board page for one party;
- the board page then sends a *session* token as `Authorization: Bearer …` on its requests
  and as the Socket.IO `auth`, for the rest of the game.

Tokens only work for the whiteboard of their party, never for the rest of the site, and
stop working when the player disconnects Discord or relinks another Discord account.
"""
import re
import secrets

from flask import current_app, g, request, session
from itsdangerous import BadSignature, URLSafeTimedSerializer

SALT = 'kw-discord-activity'
TICKET_AGE = 120
SESSION_AGE = 12 * 3600

# Everything the whiteboard page asks the server for. Each is checked against the token's party.
BOARD_ENDPOINTS = {
    'party.shared_map_scene', 'party.shared_map_tokens', 'party.shared_map_portraits',
    'party.shared_map_stats', 'party.shared_map_monster_visibility', 'party.shared_map_actor',
    'party.shared_map_character', 'party.shared_map_roll_actors', 'party.shared_map_actors',
    'party.shared_map_roll', 'party.shared_map_sources', 'party.shared_map_preview',
    'party.shared_map_import', 'party.shared_map_fog', 'party.warden_roll',
    'party.shared_map_sheets', 'party.shared_map_sheet_action',
}
BOARD_PAGE = 'activity.board'

# esm.sh modules import each other by root-relative paths ("/react@18.3.1/…"). Behind the
# Activity proxy those reach Kettlewright, which sends them on to Discord's /esm mapping.
# esm.sh also serves Node polyfills such as /node/process.mjs.
ESM_PATH = re.compile(r'^((@[a-z0-9][\w.-]*/)?[a-z0-9][\w.-]*@[^/]+(/|$)|node/[\w.-]+\.mjs$)', re.I)

# The whiteboard's bare imports, as root-relative esm.sh paths. `deps` pins React so that
# Excalidraw and the board share one React and one ReactDOM, as the import map does on the site.
ESM_IMPORTS = {
    'react': '/react@18.3.1',
    'react/jsx-runtime': '/react@18.3.1/jsx-runtime',
    'react-dom': '/react-dom@18.3.1?deps=react@18.3.1',
    'react-dom/client': '/react-dom@18.3.1/client?deps=react@18.3.1',
    'excalidraw': '/@excalidraw/excalidraw@0.18.0/dist/prod/index.js?deps=react@18.3.1,react-dom@18.3.1',
}
_BARE = re.compile(r'''((?:\bfrom|\bimport)\s*\(?\s*)(['"])(%s)\2''' % '|'.join(map(re.escape, ESM_IMPORTS)))


def _serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt=SALT)


def issue(kind, user_id, party_id, discord_id, csrf=None):
    """A signed ticket or session token. Each carries its own CSRF secret (there is no cookie session)."""
    return _serializer().dumps({'k': kind, 'u': user_id, 'p': party_id, 'd': discord_id,
                                'c': csrf or secrets.token_hex(20)})


def read(token, kind):
    """The token's claims, or None if it is invalid, expired, of another kind, or its Discord link is gone."""
    from app.models import DiscordAccount, db
    if not isinstance(token, str) or not token or len(token) > 1000:
        return None
    try:
        claims = _serializer().loads(token, max_age=TICKET_AGE if kind == 'ticket' else SESSION_AGE)
    except BadSignature:
        return None
    if not isinstance(claims, dict) or claims.get('k') != kind:
        return None
    account = db.session.get(DiscordAccount, claims.get('u'))
    if account is None or account.discord_id != claims.get('d'):
        return None
    return claims


def _request_party():
    party = (request.view_args or {}).get('party_id')
    if party is None and request.endpoint == 'party.warden_roll':
        party = request.form.get('party_id', type=int)
    return party


def load_request_user(req):
    """Flask-Login request loader: a whiteboard request from the Activity, signed in by its token."""
    from app.models import User, db
    if req.endpoint == BOARD_PAGE:
        claims = read(req.args.get('ticket'), 'ticket')
    elif req.endpoint in BOARD_ENDPOINTS:
        header = req.headers.get('Authorization', '')
        claims = read(header[7:], 'session') if header.startswith('Bearer ') else None
    else:
        return None
    if claims is None or _request_party() != claims['p']:
        return None
    user = db.session.get(User, claims['u'])
    if user is None:
        return None
    # The page's CSRF tokens are made from, and checked against, the secret in its token.
    session['csrf_token'] = claims['c']
    g.activity = claims
    return user


def rewrite_imports(source):
    """Point the whiteboard's bare imports at esm.sh paths: Discord's CSP allows no inline import map."""
    return _BARE.sub(lambda m: m.group(1) + m.group(2) + ESM_IMPORTS[m.group(3)] + m.group(2), source)
