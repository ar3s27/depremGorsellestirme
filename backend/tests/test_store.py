from dataclasses import replace
from datetime import timedelta

from app.models import utcnow
from conftest import make_quake


def test_upsert_reports_new_changed_and_ignores_unchanged(store):
    a, b = make_quake("a"), make_quake("b", mag=3.1)
    assert store.upsert([a, b]) == ([a, b], [])
    assert store.upsert([a, b]) == ([], [])
    revised = replace(b, mag=3.3)
    assert store.upsert([a, revised]) == ([], [revised])
    assert store.get("b").mag == 3.3
    assert store.count() == 2


def test_recent_filters_by_time_magnitude_and_orders_newest_first(store):
    store.upsert([
        make_quake("old", minutes_ago=60 * 30, mag=5.0),
        make_quake("small", minutes_ago=30, mag=1.5),
        make_quake("big", minutes_ago=90, mag=4.4),
        make_quake("newest", minutes_ago=5, mag=2.2),
    ])
    day_ago = utcnow() - timedelta(hours=24)
    assert [q.id for q in store.recent(day_ago)] == ["newest", "small", "big"]
    assert [q.id for q in store.recent(day_ago, min_mag=2.0)] == ["newest", "big"]
    assert [q.id for q in store.recent(day_ago, limit=1)] == ["newest"]
    assert [q.id for q in store.recent(day_ago, until=utcnow() - timedelta(minutes=20))] == ["small", "big"]
    assert store.latest_time() < utcnow() and store.oldest_time() < day_ago


def test_subscribers(store):
    store.subscribe(1, 4.0)
    store.subscribe(2, 3.0)
    store.subscribe(1, 5.0)  # eşiği günceller
    assert store.subscription(1) == 5.0
    assert sorted(store.subscribers_for(4.5)) == [2]
    assert sorted(store.subscribers_for(5.0)) == [1, 2]
    assert store.unsubscribe(2) is True
    assert store.unsubscribe(2) is False
    assert store.subscribers_for(9) == [1]
