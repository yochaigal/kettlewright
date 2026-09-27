import json

from flask import current_app
from flask_login import current_user
from flask_socketio import emit, join_room
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models import Character, Companion, Party, db
from app.lib.socket_rate_limit import SocketRateLimiter


def party_recipient_ids(party):
    """Resolve current membership for every broadcast, including already-open tabs."""
    members = json.loads(party.members or '[]')
    owners = db.session.query(Character.owner).filter(
        Character.id.in_(members), Character.party_id == party.id
    ).all()
    return {party.owner, *(owner for (owner,) in owners)}


def notify_roll_history_changed(party):
    from app import socketio
    for user_id in party_recipient_ids(party):
        socketio.emit('roll_history_changed', {'party_id': party.id}, room=f'user_{user_id}')


# Observe committed model changes so edits, rest and inventory changes all refresh
# the party view. Register once at module import, not once per Flask app instance.
@event.listens_for(Session, 'after_flush')
def collect_party_changes(session, flush_context):
    party_ids = session.info.setdefault('changed_party_ids', set())
    for obj in session.new | session.dirty | session.deleted:
        if isinstance(obj, Character):
            party_ids.add(obj.party_id)
            party_ids.update(inspect(obj).attrs.party_id.history.deleted)
        elif isinstance(obj, Party) and inspect(obj).attrs.members.history.has_changes():
            party_ids.add(obj.id)
    party_ids.discard(None)


@event.listens_for(Session, 'after_flush_postexec')
def resolve_party_changes(session, flush_context):
    recipients = session.info.setdefault('party_update_recipients', {})
    for party_id in session.info.pop('changed_party_ids', set()):
        party = session.get(Party, party_id)
        if party is not None:
            recipients[party_id] = party_recipient_ids(party)


@event.listens_for(Session, 'after_commit')
def publish_party_changes(session):
    from app import socketio
    for party_id, recipients in session.info.pop('party_update_recipients', {}).items():
        for user_id in recipients:
            try:
                socketio.emit('party_members_changed', {'party_id': party_id}, room=f'user_{user_id}')
            except Exception:
                # The data is already committed; a temporary transport failure
                # must not turn a successful save into an HTTP error.
                current_app.logger.exception('Unable to publish party update')


@event.listens_for(Session, 'after_rollback')
def discard_party_changes(session):
    session.info.pop('changed_party_ids', None)
    session.info.pop('party_update_recipients', None)


def register_socket_events(socketio):
    from app import redis_url
    limiter = SocketRateLimiter(redis_url)

    def allow_event(event):
        try:
            allowed = limiter.allow(
                current_user.id, event,
                current_app.config.get('SOCKET_EVENT_LIMIT', 20),
                current_app.config.get('SOCKET_EVENT_WINDOW', 10),
            )
        except Exception:
            current_app.logger.exception('Socket rate limiter unavailable')
            return False
        if not allowed:
            emit('rate_limited', {'message': 'Too many events. Please wait a moment.'})
        return allowed

    @socketio.on('connect')
    def handle_connect():
        if not current_user.is_authenticated:
            return False
        join_room(f'user_{current_user.id}')

    @socketio.on('register')
    def handle_register():
        if current_user.is_authenticated and allow_event('register'):
            join_room(f'user_{current_user.id}')

    @socketio.on('roll_dice')
    def handle_roll_dice(data):
        if not current_user.is_authenticated or not isinstance(data, dict):
            return
        if not allow_event('roll_dice'):
            return
        is_companion = data.get('companion_id') is not None
        if is_companion and data.get('character_id') is not None:
            return {'error': 'Choose either a character or a companion.'}
        try:
            actor_id = int(data.get('companion_id' if is_companion else 'character_id'))
            raw_party = data.get('party_id')
            party_id = int(raw_party) if raw_party not in (None, 'None', '') else None
        except (TypeError, ValueError):
            return
        from app.lib.character_rolls import roll_character, roll_companion, publish_roll
        actor = db.session.get(Companion if is_companion else Character, actor_id)
        try:
            if is_companion:
                result, party = roll_companion(actor, data.get('dice'), expected_party=party_id)
            else:
                result, party = roll_character(current_user.id, actor, data.get('dice'),
                                               expected_party=party_id)
        except (ValueError, PermissionError) as error:
            return {'error': str(error)}
        db.session.commit()
        publish_roll(party, actor.name, result['result'])
        return result
