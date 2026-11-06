"""AFAD deprem servisi istemcisi.

Eski sürüm AFAD'ın "son depremler" HTML sayfasını kazıyordu; sayfa düzeni değişince bozuluyordu.
Bu istemci AFAD'ın JSON servisini kullanır. Servis yalnızca yaklaşık son 1000 olayı tutar ve tek
istekte en fazla 1000 olay döndürür; uzun geçmiş bu yüzden kendi veritabanımızda birikir.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

import httpx

from .models import Quake, to_iso

log = logging.getLogger(__name__)

AFAD_URL = "https://servisnet.afad.gov.tr/apigateway/deprem/apiv2/event/filter"
PAGE_LIMIT = 1000  # servis tek yanıtta bundan fazlasını vermiyor
MIN_WINDOW = timedelta(minutes=30)
USER_AGENT = "deprem-izleme/2.0 (+https://deprem.veyselerkoyuncu.com.tr)"


class AfadError(Exception):
    pass


def _number(value) -> float:
    return float(str(value).replace(",", "."))


def _text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_event(raw: dict) -> Quake | None:
    """AFAD olayını Quake'e çevirir; eksik ya da bozuk kayıtta None döner."""
    try:
        quake_id = str(raw["eventID"]).strip()
        when = datetime.fromisoformat(str(raw["date"]))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)  # AFAD saatleri UTC verir
        lat, lon = _number(raw["latitude"]), _number(raw["longitude"])
        if not quake_id or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return Quake(
            id=quake_id,
            time=to_iso(when),
            lat=round(lat, 5),
            lon=round(lon, 5),
            depth=round(_number(raw["depth"]), 2),
            mag=round(_number(raw["magnitude"]), 1),
            mag_type=_text(raw.get("type")) or "ML",
            location=_text(raw.get("location")) or "Bilinmeyen konum",
            province=_text(raw.get("province")),
            district=_text(raw.get("district")),
            country=_text(raw.get("country")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _unique(quakes: Iterable[Quake]) -> list[Quake]:
    seen: dict[str, Quake] = {}
    for quake in quakes:
        seen[quake.id] = quake
    return list(seen.values())


class AfadClient:
    def __init__(self, url: str = AFAD_URL, http: httpx.AsyncClient | None = None):
        self.url = url
        self._owns_http = http is None
        self.http = http or httpx.AsyncClient(
            timeout=httpx.Timeout(20, connect=10),
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    async def aclose(self) -> None:
        if self._owns_http:
            await self.http.aclose()

    async def _fetch(self, start: datetime, end: datetime) -> list[dict]:
        fmt = "%Y-%m-%dT%H:%M:%S"
        params = {
            "start": start.astimezone(timezone.utc).strftime(fmt),
            "end": end.astimezone(timezone.utc).strftime(fmt),
            "orderby": "timedesc",
        }
        response = await self.http.get(self.url, params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise AfadError(f"AFAD beklenmeyen yanıt verdi: {type(data).__name__}")
        return data

    async def fetch_range(self, start: datetime, end: datetime) -> list[Quake]:
        """[start, end] aralığındaki olaylar. Dolu gelen pencere ikiye bölünüp yeniden istenir."""
        raw = await self._fetch(start, end)
        if len(raw) >= PAGE_LIMIT and end - start > MIN_WINDOW:
            middle = start + (end - start) / 2
            older = await self.fetch_range(start, middle)
            newer = await self.fetch_range(middle, end)
            return _unique(older + newer)
        if len(raw) >= PAGE_LIMIT:
            log.warning("AFAD %s..%s penceresi %d olayla kesildi", to_iso(start), to_iso(end), len(raw))
        return _unique(q for q in map(parse_event, raw) if q is not None)
