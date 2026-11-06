import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from conftest import make_quake


@pytest.fixture
def client(store, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "SSE_PING_SECONDS", 0.2)
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Sismik</title>", encoding="utf-8")
    (tmp_path / "assets" / "app-123.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    store.upsert([
        make_quake("near", minutes_ago=20, mag=2.5, lat=39.10, lon=35.05),
        make_quake("main", minutes_ago=10, mag=4.6, lat=39.00, lon=35.00, location="Kozan <Adana>"),
        make_quake("far", minutes_ago=30, mag=3.0, lat=41.00, lon=29.00),
        make_quake("old", minutes_ago=60 * 48, mag=5.2, lat=39.01, lon=35.01),
    ])
    app = main.create_app(Settings(collector_enabled=False, static_dir=str(tmp_path)), store=store)
    with TestClient(app) as test_client:
        yield test_client


def test_quakes_endpoint_filters_and_sorts(client):
    body = client.get("/api/quakes").json()
    assert [q["id"] for q in body["quakes"]] == ["main", "near", "far"]
    assert body["count"] == 3 and body["hours"] == 24
    assert body["quakes"][0]["location"] == "Kozan <Adana>"
    assert [q["id"] for q in client.get("/api/quakes?hours=72&min_mag=3").json()["quakes"]] == ["main", "far", "old"]
    assert client.get("/api/quakes?hours=0").status_code == 422


def test_quake_detail_lists_nearby_within_50_km(client):
    body = client.get("/api/quakes/main").json()
    assert body["quake"]["mag"] == 4.6
    nearby = {q["id"]: q["distance_km"] for q in body["nearby"]}
    assert set(nearby) == {"near", "old"}  # "far" İstanbul'da
    assert 0 < nearby["near"] < 15
    missing = client.get("/api/quakes/yok")
    assert missing.status_code == 404 and missing.json()["detail"] == "Deprem bulunamadı"


def test_health_and_unknown_api_paths(client):
    health = client.get("/api/health").json()
    assert health["quakes"] == 4 and health["status"] == "stale"  # toplayıcı testte kapalı
    unknown = client.get("/api/yok/boyle")
    assert unknown.status_code == 404 and unknown.headers["content-type"].startswith("application/json")


def test_frontend_routes_and_headers(client):
    index = client.get("/")
    assert "Sismik" in index.text
    assert "default-src 'self'" in index.headers["content-security-policy"]
    assert index.headers["x-frame-options"] == "DENY"
    assert client.get("/deprem/123").text == index.text  # tek sayfalık uygulama yolları
    asset = client.get("/assets/app-123.js")
    assert asset.status_code == 200 and "immutable" in asset.headers["cache-control"]
    assert client.get("/favicon.svg").text == "<svg/>"
    assert client.get("/../backend/app/main.py").text == index.text
    docs = client.get("/api/docs")
    assert docs.status_code == 200 and "cdn.jsdelivr.net" in docs.headers["content-security-policy"]
    cors = client.get("/api/quakes", headers={"Origin": "https://baska-site.example"})
    assert cors.headers["access-control-allow-origin"] == "*"  # API herkese açık


def test_stream_delivers_published_quakes(client):
    hub = client.app.state.hub
    with client.stream("GET", "/api/stream") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = response.iter_lines()
        assert next(lines) == "retry: 5000"
        client.portal.call(hub.publish, "new", make_quake("canli", minutes_ago=0, mag=3.7))
        received = []
        for line in lines:
            if line.startswith("data:"):
                received.append(line)
                break
            if line.startswith("event:"):
                received.append(line)
    assert received[0] == "event: new"
    assert '"id": "canli"' in received[1] and '"mag": 3.7' in received[1]
