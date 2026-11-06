from datetime import timedelta

import pytest

from app.models import Quake, to_iso, utcnow
from app.store import Store


def make_quake(qid: str, minutes_ago: float = 10, mag: float = 2.0, lat: float = 39.0, lon: float = 35.0, **extra) -> Quake:
    fields = dict(
        id=qid,
        time=to_iso(utcnow() - timedelta(minutes=minutes_ago)),
        lat=lat,
        lon=lon,
        depth=7.0,
        mag=mag,
        mag_type="ML",
        location="Simav (Kütahya)",
        province="Kütahya",
        district="Simav",
        country="Türkiye",
    )
    fields.update(extra)
    return Quake(**fields)


@pytest.fixture
def store():
    s = Store(":memory:")
    yield s
    s.close()
