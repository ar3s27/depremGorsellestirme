from fastapi import FastAPI
import requests as re
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

kutuphane = {}

@app.get('/')
def earthquake():
    while True:
        url = "https://deprem.afad.gov.tr/last-earthquakes.html"
        response = re.get(url)
        try:
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                table = soup.find("table")
                rows = table.find_all("tr")[1:]  # Skip the first row (header)
                last_10_rows = rows[:10]  # Get the last 10 rows
                
                earthquakes = {}
                for row in last_10_rows:
                    cells = row.find_all("td")

                    if cells:
                        location = cells[6].text.strip()
                        date = cells[0].text.strip()
                        latitude = cells[1].text.strip()
                        longitude = cells[2].text.strip()
                        depth = cells[3].text.strip()
                        magnitude = cells[5].text.strip()
                        quake_id = str(uuid.uuid4())
                        if quake_id in kutuphane:
                            continue
                        else: 
                            earthquake_data = {
                                "quake_id": quake_id,
                                "location": location,
                                "latitude": latitude,
                                "longitude": longitude,
                                "depth": depth,
                                "magnitude": magnitude,
                                "date": date
                            }
                            earthquakes[quake_id] = earthquake_data
                
                kutuphane.update(earthquakes)
                
                return earthquakes
            else:
                return {"error": "Failed to fetch earthquake data"}

        except AttributeError:
            print("Table not found. Check the website structure.")