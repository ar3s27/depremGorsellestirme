"""Telegram mesaj metinleri (HTML biçimi). aiogram'dan bağımsız, test edilebilir."""
from __future__ import annotations

from datetime import datetime
from html import escape
from urllib.parse import quote

from .models import TRT, Quake


def relative_tr(when: datetime, now: datetime) -> str:
    seconds = (now - when).total_seconds()
    if seconds < 60:
        return "az önce"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} dk önce"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} sa önce"
    return f"{hours // 24} gün önce"


def local_time(when: datetime) -> str:
    return when.astimezone(TRT).strftime("%d.%m %H:%M")


def mag_mark(mag: float) -> str:
    if mag >= 5:
        return "🔴"
    if mag >= 4:
        return "🟠"
    if mag >= 3:
        return "🟡"
    return "⚪"


def quake_url(public_url: str, quake: Quake) -> str:
    return f"{public_url}/?q={quote(quake.id)}"


def quake_line(quake: Quake, now: datetime, public_url: str, distance_km: float | None = None) -> str:
    when = quake.dt
    extra = f" · {distance_km:.0f} km uzakta" if distance_km is not None else ""
    return (
        f"{mag_mark(quake.mag)} <b>M{quake.mag:.1f}</b> {escape(quake.location)}\n"
        f"      {local_time(when)} · {relative_tr(when, now)} · {quake.depth:.0f} km derinlik{extra} · "
        f'<a href="{escape(quake_url(public_url, quake))}">harita</a>'
    )


def quake_list(title: str, quakes: list[Quake], now: datetime, public_url: str, distances: dict[str, float] | None = None) -> str:
    lines = [f"<b>{escape(title)}</b>", ""]
    for quake in quakes:
        lines.append(quake_line(quake, now, public_url, (distances or {}).get(quake.id)))
    lines += ["", "Saatler Türkiye saatidir (TSİ). Kaynak: AFAD"]
    return "\n".join(lines)


def alert_text(quake: Quake, public_url: str) -> str:
    return (
        f"{mag_mark(quake.mag)} <b>Deprem: M{quake.mag:.1f}</b>\n"
        f"{escape(quake.location)}\n"
        f"{local_time(quake.dt)} TSİ · {quake.depth:.0f} km derinlik\n"
        f'<a href="{escape(quake_url(public_url, quake))}">Haritada gör</a>'
    )


def parse_magnitude(text: str | None, default: float, low: float, high: float) -> float | None:
    """'/abone 4,5' gibi girdiyi okur; geçersizse None, aralık dışıysa sınıra çeker."""
    if not text or not text.strip():
        return default
    try:
        value = float(text.strip().replace(",", "."))
    except ValueError:
        return None
    return min(max(value, low), high)
