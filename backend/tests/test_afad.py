import asyncio
from datetime import datetime, timezone

import httpx

from app.afad import PAGE_LIMIT, AfadClient, parse_event

SAMPLE = {
    "rms": "0.86", "eventID": "598464", "location": "Akdeniz", "latitude": "34.4885", "longitude": "25.227",
    "depth": "5.11", "type": "ML", "magnitude": "3.4", "country": None, "province": "Muğla",
    "district": "Datça", "neighborhood": None, "date": "2026-11-06T22:24:14", "isEventUpdate": False,
    "lastUpdateDate": None,
}


def test_parse_event_reads_afad_fields_as_utc():
    quake = parse_event(SAMPLE)
    assert quake is not None
    assert quake.id == "598464"
    assert quake.time == "2026-11-06T22:24:14Z"
    assert (quake.lat, quake.lon, quake.depth, quake.mag) == (34.4885, 25.227, 5.11, 3.4)
    assert quake.mag_type == "ML" and quake.province == "Muğla" and quake.country is None


def test_parse_event_accepts_decimal_commas_and_rejects_broken_rows():
    assert parse_event({**SAMPLE, "magnitude": "4,2"}).mag == 4.2
    assert parse_event({**SAMPLE, "latitude": None}) is None
    assert parse_event({**SAMPLE, "latitude": "123"}) is None
    assert parse_event({**SAMPLE, "date": "dün"}) is None
    missing = dict(SAMPLE)
    del missing["eventID"]
    assert parse_event(missing) is None


def test_fetch_range_splits_full_windows_and_deduplicates():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        start = datetime.fromisoformat(request.url.params["start"])
        end = datetime.fromisoformat(request.url.params["end"])
        calls.append((start, end))
        hours = (end - start).total_seconds() / 3600
        if hours > 12:  # geniş pencere: servis sınırına takılmış gibi davran
            rows = [{**SAMPLE, "eventID": str(i)} for i in range(PAGE_LIMIT)]
        else:  # dar pencerede gerçek kayıtlar; sınırdaki olay iki parçada da geliyor
            rows = [{**SAMPLE, "eventID": f"{start:%H}"}, {**SAMPLE, "eventID": "sinir"}]
        return httpx.Response(200, json=rows)

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        client = AfadClient("https://afad.test/filter", http=http)
        try:
            return await client.fetch_range(
                datetime(2026, 11, 5, tzinfo=timezone.utc), datetime(2026, 11, 6, tzinfo=timezone.utc)
            )
        finally:
            await http.aclose()

    quakes = asyncio.run(run())
    assert len(calls) == 3  # 24 sa dolu geldi -> iki 12 saatlik parça
    assert sorted(q.id for q in quakes) == ["00", "12", "sinir"]
    assert calls[0][0].isoformat() == "2026-11-05T00:00:00"
