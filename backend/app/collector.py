"""AFAD'dan düzenli veri çeken arka plan görevi."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from .afad import AfadClient
from .hub import Hub
from .models import to_iso, utcnow
from .store import Store

log = logging.getLogger(__name__)

# Her turda son 24 saat yeniden istenir: AFAD sonradan büyüklük/konum düzeltmesi yapabiliyor.
POLL_WINDOW = timedelta(hours=24)
MAX_BACKOFF = 600


class Collector:
    def __init__(self, store: Store, client: AfadClient, hub: Hub, poll_seconds: int = 60, backfill_days: int = 14):
        self.store = store
        self.client = client
        self.hub = hub
        self.poll_seconds = poll_seconds
        self.backfill_days = backfill_days
        self.last_success: datetime | None = None
        self.last_error: str | None = None
        self.last_error_at: datetime | None = None

    async def backfill(self) -> int:
        """Eksik günleri günlük parçalarla tamamlar. İlk açılışta AFAD'ın tuttuğu tüm geçmiş gelir;
        sonraki açılışlarda yalnızca kapalı kalınan süre. Bunlar için uyarı/yayın yapılmaz."""
        now = utcnow()
        oldest = now - timedelta(days=self.backfill_days)
        latest = await asyncio.to_thread(self.store.latest_time)
        start = oldest if latest is None else max(oldest, latest - timedelta(days=1))
        added = 0
        while start < now:
            end = min(start + timedelta(days=1), now)
            quakes = await self.client.fetch_range(start, end)
            new, _ = await asyncio.to_thread(self.store.upsert, quakes)
            added += len(new)
            start = end
        log.info("Geçmiş tamamlandı: %d yeni deprem (%s sonrası)", added, to_iso(oldest))
        return added

    async def poll_once(self) -> tuple[int, int]:
        now = utcnow()
        quakes = await self.client.fetch_range(now - POLL_WINDOW, now + timedelta(minutes=5))
        new, changed = await asyncio.to_thread(self.store.upsert, quakes)
        for quake in sorted(new, key=lambda q: q.time):
            self.hub.publish("new", quake)
        for quake in changed:
            self.hub.publish("update", quake)
        self.last_success = utcnow()
        self.last_error = None
        if new or changed:
            log.info("AFAD: %d yeni, %d güncellenen deprem", len(new), len(changed))
        return len(new), len(changed)

    def _failed(self, error: Exception) -> None:
        self.last_error = f"{type(error).__name__}: {error}"
        self.last_error_at = utcnow()
        log.warning("AFAD isteği başarısız: %s", self.last_error)

    async def run(self) -> None:
        try:
            await self.backfill()
        except Exception as error:  # geçmiş eksik kalsa da canlı takip başlasın
            self._failed(error)
        delay = self.poll_seconds
        while True:
            try:
                await self.poll_once()
                delay = self.poll_seconds
            except Exception as error:
                self._failed(error)
                delay = min(delay * 2, MAX_BACKOFF)
            await asyncio.sleep(delay)
