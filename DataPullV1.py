from fastapi import FastAPI
import uvicorn
import requests as re
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

kutuphane = {}

@app.get('/')
def earthquake():
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    response = re.get(url)
    
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
        
        # Update the global dictionary with new earthquake data
        kutuphane.update(earthquakes)
        
        return earthquakes
    else:
        # If there's an error fetching the page, return an error message
        return {"error": "Failed to fetch earthquake data"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)
