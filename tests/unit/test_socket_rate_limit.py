from app.lib.socket_rate_limit import SocketRateLimiter


def test_limit_expires_and_is_scoped_to_user_and_event(monkeypatch):
    monkeypatch.setattr('app.lib.socket_rate_limit.monotonic', lambda: 100)
    limiter = SocketRateLimiter()
    assert limiter.allow(1, 'roll', 1, 10)
    assert not limiter.allow(1, 'roll', 1, 10)
    assert limiter.allow(2, 'roll', 1, 10)
    assert limiter.allow(1, 'register', 1, 10)
    monkeypatch.setattr('app.lib.socket_rate_limit.monotonic', lambda: 110)
    assert limiter.allow(1, 'roll', 1, 10)
    assert len(limiter.windows) == 1
