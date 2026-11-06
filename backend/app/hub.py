"""Süreç içi yayın kanalı: toplayıcı yeni/güncellenen depremleri yayınlar,
canlı akış bağlantıları (SSE) ve Telegram botu dinler."""
from __future__ import annotations

import asyncio
import logging

from .models import Quake

log = logging.getLogger(__name__)

Event = tuple[str, Quake]  # ("new" | "update", deprem)


class Hub:
    def __init__(self, queue_size: int = 200):
        self._queues: set[asyncio.Queue[Event]] = set()
        self._queue_size = queue_size

    @property
    def listeners(self) -> int:
        return len(self._queues)

    def subscribe(self) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=self._queue_size)
        self._queues.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        self._queues.discard(queue)

    def publish(self, kind: str, quake: Quake) -> None:
        for queue in list(self._queues):
            try:
                queue.put_nowait((kind, quake))
            except asyncio.QueueFull:
                # Okumayan (takılmış) bir dinleyici diğerlerini bekletmesin.
                log.warning("Yavaş dinleyici; %s olayı atlandı", quake.id)
