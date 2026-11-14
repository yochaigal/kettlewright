"""Show the player the dice the server just rolled, as 3D dice in the browser (static/src/js/dice3d.js).

Rolls made by fetch/socket calls return their values directly. Rolls made inside an htmx partial or a form
that redirects call queue_dice(); the values then reach the browser after the response:
  * htmx swap: an HX-Trigger 'dice3d' event (handled by dice3d_events.js),
  * redirect or full page: kept in the session and rendered once by base.html (pending_dice).
"""
import json

from flask import g, session

SESSION_KEY = 'dice3d_pending'
MAX_DICE = 12


def queue_dice(values, sides):
    """Animate these server values (e.g. [3, 5], [6, 6]) once the response reaches the browser."""
    values, sides = list(values), list(sides) if not isinstance(sides, int) else [sides] * len(values)
    if len(values) != len(sides) or not values:
        return
    pending = g.setdefault('dice3d', {'values': [], 'sides': []})
    room = MAX_DICE - len(pending['values'])
    pending['values'].extend(values[:room])
    pending['sides'].extend(sides[:room])


def send_queued_dice(response, request):
    """after_request: hand the queued dice to the browser in the way this response can carry them."""
    pending = g.pop('dice3d', None)
    if not pending:
        return response
    if request.headers.get('HX-Request') == 'true' and not 300 <= response.status_code < 400:
        triggers = {}
        if response.headers.get('HX-Trigger'):
            raw = response.headers['HX-Trigger']
            try:
                triggers = json.loads(raw)
            except ValueError:
                triggers = {name.strip(): None for name in raw.split(',') if name.strip()}
        triggers['dice3d'] = pending
        response.headers['HX-Trigger'] = json.dumps(triggers)
    else:
        session[SESSION_KEY] = pending
    return response


def pending_dice():
    """For base.html: dice queued before a redirect (or while rendering this page), shown once."""
    return session.pop(SESSION_KEY, None) or g.pop('dice3d', None)
