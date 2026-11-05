import time
import uuid

import requests as re
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

AFAD_URL = "https://deprem.afad.gov.tr/last-earthquakes.html"
# AFAD'a her istekte yeniden gitmemek için sonucu kısa süre sakla.
CACHE_SECONDS = 60
_cache = {"time": 0.0, "data": None}


def quake_id(date, latitude, longitude):
    # Aynı deprem her istekte aynı kimliği alır (önceden her seferinde rastgeleydi).
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"afad:{date}:{latitude}:{longitude}"))


def fetch_earthquakes():
    """AFAD'ın son depremler tablosundan ilk 10 satırı okur; olmazsa None döner."""
    response = re.get(AFAD_URL, timeout=10)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    if table is None:
        print("Table not found. Check the website structure.")
        return None

    earthquakes = {}
    for row in table.find_all("tr")[1:11]:  # Başlığı atla, son 10 deprem
        cells = row.find_all("td")
        if len(cells) < 7:
            continue
        date = cells[0].text.strip()
        latitude = cells[1].text.strip()
        longitude = cells[2].text.strip()
        qid = quake_id(date, latitude, longitude)
        earthquakes[qid] = {
            "quake_id": qid,
            "location": cells[6].text.strip(),
            "latitude": latitude,
            "longitude": longitude,
            "depth": cells[3].text.strip(),
            "magnitude": cells[5].text.strip(),
            "date": date,
        }
    return earthquakes


@app.get('/')
def earthquake():
    now = time.monotonic()
    if _cache["data"] is not None and now - _cache["time"] < CACHE_SECONDS:
        return _cache["data"]

    try:
        data = fetch_earthquakes()
    except re.RequestException as e:
        print(f"AFAD isteği başarısız: {e}")
        data = None

    if data is None:
        # AFAD'a ulaşılamazsa son başarılı sonucu ver; o da yoksa hata.
        if _cache["data"] is not None:
            return _cache["data"]
        return {"error": "Failed to fetch earthquake data"}

    _cache["time"], _cache["data"] = now, data
    return data
