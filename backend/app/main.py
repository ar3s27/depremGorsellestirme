"""Web uygulaması: JSON API, canlı akış (SSE) ve derlenmiş ön yüz.

Çalıştırma:  uvicorn app.main:create_app --factory --port 8000
"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders

from .afad import AfadClient
from .collector import Collector
from .config import Settings
from .hub import Hub
from .models import distance_km, to_iso, utcnow
from .store import Store

log = logging.getLogger("deprem")

NEARBY_KM = 50
SSE_PING_SECONDS = 20  # Cloudflare boşta kalan bağlantıyı ~100 sn'de keser

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://static.cloudflareinsights.com",
    "style-src 'self' 'unsafe-inline'",  # MapLibre ve React satır içi stil kullanıyor
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "connect-src 'self' https://tiles.openfreemap.org https://cloudflareinsights.com",
    "worker-src 'self' blob:",  # MapLibre harita işçisini blob'dan başlatıyor
    "child-src blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
# /api/docs (Swagger) betik ve stilini jsDelivr'dan yükler.
DOCS_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "img-src 'self' data: https://fastapi.tiangolo.com",
    "frame-ancestors 'none'",
])


class SecurityHeaders:
    """Saf ASGI ara katmanı (SSE akışını tamponlamaz)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path: str = scope["path"]

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=()")
                headers.setdefault("Content-Security-Policy", DOCS_CSP if path.startswith("/api/docs") else CSP)
                if path.startswith("/assets/"):
                    headers["Cache-Control"] = "public, max-age=31536000, immutable"
                elif path.startswith("/api/") and "cache-control" not in headers:
                    headers["Cache-Control"] = "no-cache"
            await send(message)

        await self.app(scope, receive, send_with_headers)


def _log_task_end(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception() is not None:
        log.error("%s görevi durdu: %r", task.get_name(), task.exception())


def create_app(settings: Settings | None = None, *, store: Store | None = None, client: AfadClient | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        # httpx her AFAD isteğini (dakikada bir), aiogram her Telegram mesajını INFO olarak yazar.
        for noisy in ("httpx", "aiogram.event"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_store = store or Store(settings.db_path)
        app_client = client or AfadClient(settings.afad_url)
        hub = Hub()
        collector = Collector(app_store, app_client, hub, settings.poll_seconds, settings.backfill_days)
        app.state.store, app.state.hub, app.state.collector = app_store, hub, collector

        tasks: list[asyncio.Task] = []
        if settings.collector_enabled:
            tasks.append(asyncio.create_task(collector.run(), name="AFAD toplayıcı"))
        if settings.telegram_token:
            from .bot import DepremBot  # aiogram yalnızca bot açıkken yüklensin

            bot = DepremBot(settings.telegram_token, app_store, hub, settings.public_url)
            tasks.append(asyncio.create_task(bot.run(), name="Telegram botu"))
        else:
            log.info("TELEGRAM_BOT_TOKEN tanımlı değil; Telegram botu kapalı")
        for task in tasks:
            task.add_done_callback(_log_task_end)
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if client is None:
                await app_client.aclose()
            if store is None:
                app_store.close()

    app = FastAPI(
        title="Deprem İzleme API",
        description="AFAD verisiyle Türkiye ve çevresindeki depremler. Kaynak: https://deprem.afad.gov.tr",
        version="2.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])
    app.add_middleware(SecurityHeaders)

    api = APIRouter(prefix="/api")

    @api.get("/quakes", summary="Son depremler (en yeniden eskiye)")
    def list_quakes(
        request: Request,
        hours: int = Query(24, ge=1, le=24 * 365, description="Kaç saat geriye"),
        min_mag: float = Query(0, ge=0, le=10, description="En küçük büyüklük"),
        limit: int = Query(5000, ge=1, le=20000),
    ):
        state = request.app.state
        quakes = state.store.recent(utcnow() - timedelta(hours=hours), min_mag, limit)
        last_success = state.collector.last_success
        return {
            "generated_at": to_iso(utcnow()),
            "source_updated_at": to_iso(last_success) if last_success else None,
            "hours": hours,
            "min_mag": min_mag,
            "count": len(quakes),
            "quakes": [quake.to_dict() for quake in quakes],
        }

    @api.get("/quakes/{quake_id}", summary="Tek deprem ve 50 km içindeki ±7 gün depremleri")
    def quake_detail(quake_id: str, request: Request):
        store_ = request.app.state.store
        quake = store_.get(quake_id)
        if quake is None:
            raise HTTPException(404, "Deprem bulunamadı")
        window = store_.recent(quake.dt - timedelta(days=7), until=quake.dt + timedelta(days=7))
        nearby = []
        for other in window:
            if other.id == quake.id:
                continue
            km = distance_km(quake.lat, quake.lon, other.lat, other.lon)
            if km <= NEARBY_KM:
                nearby.append({**other.to_dict(), "distance_km": round(km, 1)})
        return {"quake": quake.to_dict(), "nearby": nearby[:50]}

    @api.get("/health", summary="Servis ve veri durumu")
    def health(request: Request):
        state = request.app.state
        collector: Collector = state.collector
        stale = collector.last_success is None or utcnow() - collector.last_success > timedelta(minutes=10)
        latest, oldest = state.store.latest_time(), state.store.oldest_time()
        return {
            "status": "stale" if stale else "ok",
            "quakes": state.store.count(),
            "latest_quake": to_iso(latest) if latest else None,
            "history_since": to_iso(oldest) if oldest else None,
            "last_success": to_iso(collector.last_success) if collector.last_success else None,
            "last_error": collector.last_error,
            "live_listeners": state.hub.listeners,
        }

    @api.get("/stream", summary="Canlı akış (Server-Sent Events): new / update olayları")
    async def stream(request: Request):
        hub: Hub = request.app.state.hub
        queue = hub.subscribe()

        async def events():
            try:
                yield "retry: 5000\n\n"
                while not await request.is_disconnected():
                    try:
                        kind, quake = await asyncio.wait_for(queue.get(), timeout=SSE_PING_SECONDS)
                    except TimeoutError:
                        yield ": ping\n\n"
                        continue
                    data = json.dumps(quake.to_dict(), ensure_ascii=False)
                    yield f"event: {kind}\ndata: {data}\n\n"
            finally:
                hub.unsubscribe(queue)

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @api.get("/{rest:path}", include_in_schema=False)
    def api_not_found(rest: str):
        raise HTTPException(404, "Böyle bir API adresi yok")

    app.include_router(api)

    static = Path(settings.static_dir).resolve() if settings.static_dir else None
    if static and (static / "index.html").is_file():
        index = static / "index.html"
        if (static / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

        @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
        def frontend(path: str):
            # Kök klasördeki dosyalar (favicon vb.) olduğu gibi; diğer her yol tek sayfalık uygulamaya.
            candidate = (static / path).resolve()
            if path and candidate.is_file() and candidate.parent == static:
                return FileResponse(candidate, headers={"Cache-Control": "public, max-age=3600"})
            return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return app
