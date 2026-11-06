"""Deprem kaydı ve zaman / mesafe yardımcıları."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

# Türkiye 2016'dan beri yıl boyu UTC+3 (yaz saati yok); tz veritabanına gerek kalmasın diye sabit.
TRT = timezone(timedelta(hours=3), "TSİ")
ISO = "%Y-%m-%dT%H:%M:%SZ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_iso(dt: datetime) -> str:
    """UTC, saniye hassasiyetinde, sonu Z: metin olarak sıralandığında zamana göre sıralanır."""
    return dt.astimezone(timezone.utc).strftime(ISO)


def from_iso(value: str) -> datetime:
    return datetime.strptime(value, ISO).replace(tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class Quake:
    id: str
    time: str  # UTC, ISO 8601 (to_iso biçimi)
    lat: float
    lon: float
    depth: float  # km
    mag: float
    mag_type: str  # ML, MW, ...
    location: str
    province: str | None = None
    district: str | None = None
    country: str | None = None

    @property
    def dt(self) -> datetime:
        return from_iso(self.time)

    def to_dict(self) -> dict:
        return asdict(self)


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki nokta arasındaki büyük çember mesafesi (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))
