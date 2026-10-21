import os
from time import sleep
from uuid import uuid4
import pytest
from app.lib.whiteboard_presence import WhiteboardPresence


def test_local_leases_expire_and_are_renewable():
    clock = [100]
    store = WhiteboardPresence(now=lambda: clock[0])
    record = dict(party_id=1, scene_id=2, user_id=3, visible=True)
    store.put('one', record)
    clock[0] = 159
    assert len(store.records()) == 1
    clock[0] = 160
    assert store.records() == []
    store.put('one', {**record, 'visible': False})
    assert store.records()[0]['visible'] is False
    store.remove('one'); assert store.records() == []


@pytest.mark.skipif(not os.environ.get('WHITEBOARD_TEST_REDIS_URL'), reason='Set WHITEBOARD_TEST_REDIS_URL for isolated Redis integration')
def test_redis_workers_share_leases_and_expiry():
    first, second = [WhiteboardPresence(os.environ['WHITEBOARD_TEST_REDIS_URL']) for _ in range(2)]
    first.prefix = second.prefix = f'kettlewright:qa-presence:{uuid4().hex}:'
    record = dict(party_id=1, scene_id=2, user_id=3, visible=True)
    try:
        first.put('one', record)
        second.put('two', {**record, 'visible': False})
        assert len(first.records()) == len(second.records()) == 2
        assert 0 < first.redis.ttl(first.prefix + 'one') <= 60
        first.remove('one')
        assert second.records()[0]['visible'] is False
        second.redis.pexpire(second.prefix + 'two', 10)
        sleep(.03)
        assert first.records() == []
    finally:
        first.remove('one'); second.remove('two')
