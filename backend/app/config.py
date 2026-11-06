"""Ayarlar ortam değişkenlerinden okunur (sunucuda compose.yaml ve .env)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from .afad import AFAD_URL


@dataclass(frozen=True)
class Settings:
    db_path: str = "data/deprem.sqlite3"
    afad_url: str = AFAD_URL
    poll_seconds: int = 60
    backfill_days: int = 14
    collector_enabled: bool = True
    telegram_token: str = ""
    public_url: str = "https://deprem.veyselerkoyuncu.com.tr"
    static_dir: str = ""  # derlenmiş ön yüz (frontend/dist); boşsa yalnızca API çalışır

    @classmethod
    def from_env(cls) -> Settings:
        env = os.environ.get
        return cls(
            db_path=env("DB_PATH", cls.db_path),
            afad_url=env("AFAD_URL", cls.afad_url),
            poll_seconds=int(env("POLL_SECONDS", cls.poll_seconds)),
            backfill_days=int(env("BACKFILL_DAYS", cls.backfill_days)),
            collector_enabled=env("COLLECTOR", "1") != "0",
            telegram_token=env("TELEGRAM_BOT_TOKEN", "").strip(),
            public_url=env("PUBLIC_URL", cls.public_url).rstrip("/"),
            static_dir=env("STATIC_DIR", cls.static_dir),
        )
