"""Ephemeral per-socket leases, shared between workers when Redis is enabled."""
import json
from threading import RLock
from time import time


class WhiteboardPresence:
    ttl = 60
    prefix = 'kettlewright:whiteboard-presence:'

    def __init__(self, redis_url=None, now=time):
        self.now, self.local, self.lock = now, {}, RLock()
        self.redis = None
        if redis_url:
            from redis import Redis
            self.redis = Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)

    def put(self, sid, value):
        record = {**value, 'expires': self.now() + self.ttl}
        with self.lock:
            self.local[sid] = record
        if self.redis is not None:
            self.redis.set(self.prefix + sid, json.dumps(record), ex=self.ttl)

    def remove(self, sid):
        with self.lock:
            record = self.local.pop(sid, None)
        if self.redis is not None:
            self.redis.delete(self.prefix + sid)
        return record

    def records(self):
        if self.redis is not None:
            keys = list(self.redis.scan_iter(match=self.prefix + '*', count=100))
            return [json.loads(value) for value in self.redis.mget(keys) if value] if keys else []
        with self.lock:
            return [dict(record) for record in self.local.values() if record['expires'] > self.now()]

    def owned(self):
        with self.lock:
            return list(self.local.items())


def register_presence(socketio, limiter, redis_url):
    from flask import current_app, request
    from flask_login import current_user
    from flask_socketio import emit
    from flask_wtf.csrf import validate_csrf
    from wtforms.validators import ValidationError
    from werkzeug.exceptions import HTTPException
    from app.models import db, Party, PartyMap, WhiteboardScene
    from app.lib.whiteboard_scenes import context
    from app.socket_events import party_recipient_ids
    app = current_app._get_current_object()
    store = WhiteboardPresence(redis_url)
    app.extensions['whiteboard_presence'] = store
    started = False

    def notify(record):
        if not record:
            return
        party = db.session.get(Party, record['party_id'])
        board = db.session.get(PartyMap, record['party_id'])
        if party is None or board is None:
            return
        recipients = party_recipient_ids(party) if board.active_scene_id == record['scene_id'] else {party.owner}
        for user_id in recipients:
            socketio.emit('whiteboard_presence_changed', {'party_id': party.id, 'scene_id': record['scene_id']}, room=f'user_{user_id}')

    def maintain():
        while True:
            socketio.sleep(15)
            with app.app_context():
                try:
                    for sid, record in store.owned():
                        party = db.session.get(Party, record['party_id'])
                        board = db.session.get(PartyMap, record['party_id'])
                        scene = db.session.get(WhiteboardScene, record['scene_id'])
                        if (not socketio.server.manager.is_connected(sid, '/') or party is None or scene is None
                            or record['user_id'] not in party_recipient_ids(party)
                            or record['user_id'] != party.owner and board.active_scene_id != scene.id):
                            notify(store.remove(sid))
                        else:
                            store.put(sid, record)
                except Exception:
                    app.logger.exception('Unable to renew Whiteboard presence')
                finally:
                    db.session.remove()

    @socketio.on('whiteboard_presence')
    def presence(data):
        nonlocal started
        if not current_user.is_authenticated or not isinstance(data, dict):
            return
        try:
            if not limiter.allow(current_user.id, 'whiteboard_presence', 30, 10):
                return
            if current_app.config.get('WTF_CSRF_ENABLED', True):
                validate_csrf(data.get('csrf_token'))
            if data.get('leave') is True:
                notify(store.remove(request.sid))
                return {'ok': True}
            if type(data.get('party_id')) is not int or type(data.get('visible')) is not bool:
                return
            party, board, scene = context(data['party_id'], data)
            old = store.remove(request.sid)
            record = {'party_id': party.id, 'scene_id': scene.id, 'user_id': current_user.id, 'visible': data['visible']}
            store.put(request.sid, record)
            notify(old)
            notify(record)
            if not started and not app.testing:
                started = True
                socketio.start_background_task(maintain)
            return {'ok': True}
        except (HTTPException, ValidationError):
            return {'error': 'access_denied'}
        except Exception:
            app.logger.exception('Whiteboard presence unavailable')
            return {'error': 'unavailable'}

    @socketio.on('disconnect')
    def disconnect(reason=None):
        try:
            notify(store.remove(request.sid))
        except Exception:
            app.logger.exception('Unable to clear Whiteboard presence')
