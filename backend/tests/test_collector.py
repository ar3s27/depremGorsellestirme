import asyncio
from dataclasses import replace
from datetime import timedelta

from app.collector import Collector
from app.hub import Hub
from conftest import make_quake


class FakeAfad:
    def __init__(self):
        self.quakes = []
        self.calls = []

    async def fetch_range(self, start, end):
        self.calls.append((start, end))
        return [q for q in self.quakes if start <= q.dt <= end]


def test_poll_publishes_new_then_updated_quakes(store):
    async def run():
        afad, hub = FakeAfad(), Hub()
        collector = Collector(store, afad, hub)
        queue = hub.subscribe()
        later, earlier = make_quake("2", minutes_ago=5), make_quake("1", minutes_ago=50)
        afad.quakes = [later, earlier]
        assert await collector.poll_once() == (2, 0)
        events = [queue.get_nowait(), queue.get_nowait()]
        assert [(kind, q.id) for kind, q in events] == [("new", "1"), ("new", "2")]  # eskiden yeniye

        afad.quakes = [replace(later, mag=3.0), earlier]
        assert await collector.poll_once() == (0, 1)
        kind, quake = queue.get_nowait()
        assert (kind, quake.id, quake.mag) == ("update", "2", 3.0)
        assert queue.empty()
        assert collector.last_success is not None and collector.last_error is None

    asyncio.run(run())


def test_backfill_fills_days_silently_and_resumes_from_latest(store):
    async def run():
        afad, hub = FakeAfad(), Hub()
        collector = Collector(store, afad, hub, backfill_days=3)
        queue = hub.subscribe()
        afad.quakes = [make_quake("x", minutes_ago=60 * 30), make_quake("y", minutes_ago=60 * 60)]
        assert await collector.backfill() == 2
        assert len(afad.calls) == 3  # gün gün
        assert queue.empty()  # geçmiş için yayın yok

        afad.calls.clear()
        await collector.backfill()
        first_start = afad.calls[0][0]
        assert first_start > store.latest_time() - timedelta(days=1, minutes=1)

    asyncio.run(run())
