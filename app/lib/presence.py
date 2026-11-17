"""Who has Kettlewright open right now (#424), without storing anything in the database.

Every signed-in page keeps a Socket.IO connection, and its tab sends a heartbeat
every 30 seconds. A user counts as connected until TTL seconds after their last
heartbeat, so a page reload or a brief drop does not flicker them offline.

Presence is shared through Redis when it is enabled (several workers), and kept
in this process otherwise, like the socket rate limiter.
"""
from threading import Lock
from time import monotonic

TTL = 75
HEARTBEAT = 30


class Presence:
    def __init__(self, redis_url=None):
        self.expiry = {}
        self.lock = Lock()
        self.redis = None
        if redis_url:
            from redis import Redis
            self.redis = Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)

    @staticmethod
    def key(user_id):
        return f'kettlewright:presence:{user_id}'

    def touch(self, user_id):
        """Record a heartbeat. True when the user was not connected before."""
        if self.redis is not None:
            if self.redis.set(self.key(user_id), 1, ex=TTL, nx=True):
                return True
            self.redis.expire(self.key(user_id), TTL)
            return False
        now = monotonic()
        with self.lock:
            was_online = self.expiry.get(user_id, 0) > now
            self.expiry[user_id] = now + TTL
            if len(self.expiry) > 10000:  # Forget long-gone users.
                self.expiry = {uid: until for uid, until in self.expiry.items() if until > now}
            return not was_online

    def online(self, user_ids):
        """The subset of user_ids that are connected."""
        user_ids = list(dict.fromkeys(user_ids))
        if not user_ids:
            return set()
        if self.redis is not None:
            values = self.redis.mget([self.key(user_id) for user_id in user_ids])
            return {user_id for user_id, value in zip(user_ids, values) if value is not None}
        now = monotonic()
        with self.lock:
            return {user_id for user_id in user_ids if self.expiry.get(user_id, 0) > now}


_presence = None


def presence():
    global _presence
    if _presence is None:
        from app import redis_url
        _presence = Presence(redis_url)
    return _presence


def online_user_ids(user_ids):
    """Connected users among user_ids; nobody when presence is unavailable."""
    try:
        return presence().online(user_ids)
    except Exception:
        from flask import current_app
        current_app.logger.exception('Presence unavailable')
        return set()
