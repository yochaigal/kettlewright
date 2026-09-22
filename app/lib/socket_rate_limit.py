"""Per-user event limits shared by workers when Redis is enabled."""
from threading import Lock
from time import monotonic


class SocketRateLimiter:
    def __init__(self, redis_url=None):
        self.windows = {}
        self.lock = Lock()
        self.redis = None
        if redis_url:
            from redis import Redis
            self.redis = Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)

    def allow(self, user_id, event, limit, seconds):
        key = f'kettlewright:socket-limit:{user_id}:{event}'
        if self.redis is not None:
            # Set expiry atomically with the first increment, across all workers.
            count = self.redis.eval('''
                local count = redis.call('INCR', KEYS[1])
                if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
                return count
            ''', 1, key, seconds)
            return count <= limit
        now = monotonic()
        with self.lock:
            self.windows = {k: v for k, v in self.windows.items() if v[0] > now}
            expiry, count = self.windows.get(key, (now + seconds, 0))
            self.windows[key] = (expiry, count + 1)
            return count < limit
