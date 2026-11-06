"""Telegram botu (aiogram 3). Web servisiyle aynı süreçte, aynı veritabanını kullanarak çalışır.

Komutlar: /son, /buyukler, /abone [büyüklük], /iptal; konum gönderilirse 100 km içindeki depremler.
Aboneler, eşiklerini geçen yeni depremlerde anında uyarı alır.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, KeyboardButton, Message, ReplyKeyboardMarkup

from . import textfmt
from .hub import Hub
from .models import Quake, distance_km, utcnow
from .store import Store

log = logging.getLogger(__name__)

DEFAULT_ALERT_MAG = 4.0
MIN_ALERT_MAG = 2.0  # daha küçüğü günde onlarca mesaj demek
MAX_ALERT_MAG = 8.0
NEAR_KM = 100
ALERT_MAX_AGE = timedelta(minutes=30)  # servis bir süre kapalı kaldıysa eski depremler için uyarı yağmasın

BTN_RECENT = "🕑 Son depremler"
BTN_BIG = "⚠️ Büyük depremler"
BTN_NEAR = "📍 Yakınımdaki depremler"

KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_NEAR, request_location=True)],
        [KeyboardButton(text=BTN_RECENT), KeyboardButton(text=BTN_BIG)],
    ],
    resize_keyboard=True,
)

HELP = (
    "<b>Deprem botu</b> — AFAD verisiyle Türkiye ve çevresindeki depremler.\n\n"
    "/son — son 10 deprem\n"
    "/buyukler — son 7 günün 4 ve üzeri depremleri\n"
    "/abone 4.5 — bu büyüklük ve üzerinde yeni deprem olunca haber ver (varsayılan 4)\n"
    "/iptal — uyarıları kapat\n"
    "📍 Konumunu gönderirsen 100 km içindeki son 7 günün depremlerini listelerim.\n\n"
    "Harita: {url}"
)


class DepremBot:
    def __init__(self, token: str, store: Store, hub: Hub, public_url: str):
        self.store = store
        self.hub = hub
        self.public_url = public_url
        self.bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True))
        self.dp = Dispatcher()
        router = Router()
        router.message(CommandStart())(self.cmd_help)
        router.message(Command("yardim", "help"))(self.cmd_help)
        router.message(Command("son", "sondepremler"))(self.cmd_recent)
        router.message(F.text == BTN_RECENT)(self.cmd_recent)
        router.message(Command("buyukler"))(self.cmd_big)
        router.message(F.text == BTN_BIG)(self.cmd_big)
        router.message(Command("abone"))(self.cmd_subscribe)
        router.message(Command("iptal"))(self.cmd_unsubscribe)
        router.message(F.location)(self.on_location)
        self.dp.include_router(router)

    # ── komutlar ─────────────────────────────────────────────────────────

    async def cmd_help(self, message: Message) -> None:
        await message.answer(HELP.format(url=self.public_url), reply_markup=KEYBOARD)

    async def cmd_recent(self, message: Message) -> None:
        now = utcnow()
        quakes = await asyncio.to_thread(self.store.recent, now - timedelta(days=2), 0.0, 10)
        if not quakes:
            await message.answer("Son 2 günde kayıtlı deprem yok ya da veriye şu an ulaşılamıyor.")
            return
        await message.answer(textfmt.quake_list("Son 10 deprem", quakes, now, self.public_url))

    async def cmd_big(self, message: Message) -> None:
        now = utcnow()
        quakes = await asyncio.to_thread(self.store.recent, now - timedelta(days=7), 4.0, 15)
        if not quakes:
            await message.answer("Son 7 günde 4 ve üzeri büyüklükte deprem olmadı.")
            return
        await message.answer(textfmt.quake_list("Son 7 günün 4+ depremleri", quakes, now, self.public_url))

    async def cmd_subscribe(self, message: Message, command: CommandObject) -> None:
        mag = textfmt.parse_magnitude(command.args, DEFAULT_ALERT_MAG, MIN_ALERT_MAG, MAX_ALERT_MAG)
        if mag is None:
            await message.answer("Büyüklüğü sayı olarak yaz, örneğin: /abone 4.5")
            return
        await asyncio.to_thread(self.store.subscribe, message.chat.id, mag)
        await message.answer(
            f"Tamam. <b>M{mag:.1f}</b> ve üzeri yeni depremlerde haber vereceğim.\n"
            f"Eşiği değiştirmek için /abone ile yeni değeri yaz, kapatmak için /iptal."
        )

    async def cmd_unsubscribe(self, message: Message) -> None:
        removed = await asyncio.to_thread(self.store.unsubscribe, message.chat.id)
        await message.answer("Uyarılar kapatıldı." if removed else "Zaten uyarı aboneliğin yok.")

    async def on_location(self, message: Message) -> None:
        lat, lon = message.location.latitude, message.location.longitude
        now = utcnow()
        quakes = await asyncio.to_thread(self.store.recent, now - timedelta(days=7))
        near: list[tuple[Quake, float]] = []
        for quake in quakes:
            km = distance_km(lat, lon, quake.lat, quake.lon)
            if km <= NEAR_KM:
                near.append((quake, km))
        if not near:
            await message.answer(f"Son 7 günde {NEAR_KM} km içinde deprem kaydı yok.")
            return
        # En büyük 10 tanesi (eşit büyüklükte yenisi önce), listede yeniden eskiye sıralı.
        near.sort(key=lambda item: item[0].time, reverse=True)
        near.sort(key=lambda item: item[0].mag, reverse=True)
        top = sorted(near[:10], key=lambda item: item[0].time, reverse=True)
        title = f"{NEAR_KM} km içindeki son 7 günün depremleri ({len(near)} kayıt, en büyük 10'u)"
        distances = {quake.id: km for quake, km in top}
        await message.answer(textfmt.quake_list(title, [q for q, _ in top], now, self.public_url, distances))

    # ── uyarılar ─────────────────────────────────────────────────────────

    async def _send(self, chat_id: int, text: str) -> None:
        for _ in range(2):
            try:
                await self.bot.send_message(chat_id, text)
                return
            except TelegramRetryAfter as error:
                await asyncio.sleep(error.retry_after)
            except TelegramForbiddenError:
                # Kullanıcı botu engellemiş ya da sohbeti silmiş.
                await asyncio.to_thread(self.store.unsubscribe, chat_id)
                return
            except TelegramAPIError as error:
                log.warning("Uyarı gönderilemedi (%s): %s", chat_id, error)
                return

    async def _alerts(self) -> None:
        queue = self.hub.subscribe()
        try:
            while True:
                kind, quake = await queue.get()
                if kind != "new" or utcnow() - quake.dt > ALERT_MAX_AGE:
                    continue
                chat_ids = await asyncio.to_thread(self.store.subscribers_for, quake.mag)
                text = textfmt.alert_text(quake, self.public_url)
                for chat_id in chat_ids:
                    await self._send(chat_id, text)
                    await asyncio.sleep(0.05)  # Telegram'ın saniyede ~30 mesaj sınırının altında kal
        finally:
            self.hub.unsubscribe(queue)

    async def run(self) -> None:
        alerts = asyncio.create_task(self._alerts(), name="Telegram uyarıları")
        try:
            await self.bot.set_my_commands([
                BotCommand(command="son", description="Son 10 deprem"),
                BotCommand(command="buyukler", description="Son 7 günün 4+ depremleri"),
                BotCommand(command="abone", description="Yeni depremlerde uyarı al (ör. /abone 4.5)"),
                BotCommand(command="iptal", description="Uyarıları kapat"),
                BotCommand(command="yardim", description="Komutlar"),
            ])
            log.info("Telegram botu başlıyor")
            await self.dp.start_polling(self.bot, handle_signals=False)
        finally:
            alerts.cancel()
            with suppress(asyncio.CancelledError):
                await alerts
            await self.bot.session.close()
