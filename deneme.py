from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

kutuphane = {}

@app.get('/last_11_earthquakes')
def last_11_earthquakes():
    while True:
        url = "https://deprem.afad.gov.tr/last-earthquakes.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        try:
            table = soup.find("table")
            rows = table.find_all("tr")

            earthquakes = []

            for i, row in enumerate(rows[:11]):
                cells = row.find_all("td")

                if cells:
                    location = cells[6].text.strip()
                    date = cells[0].text.strip()
                    latitude = cells[1].text.strip()
                    longitude = cells[2].text.strip()
                    depth = cells[3].text.strip()
                    magnitude = cells[5].text.strip()
                    quake_id = cells[7].text.strip()

                    if quake_id in kutuphane:
                        continue
                    else:
                        print("Yer: " + location)
                        print("Enlem: " + latitude)
                        print("Boylam: " + longitude)
                        print("Derinlik: " + depth)
                        print("Büyüklük: " + magnitude)
                        print("Tarih: " + date)
                        print("\n")

                        earthquake_info = {
                            'quake_id': quake_id,
                            "location": location,
                            "latitude": latitude,
                            "longitude": longitude,
                            "depth": depth,
                            "magnitude": magnitude,
                            "date": date
                        }

                        earthquakes.append(earthquake_info)
                        kutuphane[quake_id] = earthquake_info

            return {"last_11_earthquakes": earthquakes}
            time.sleep(600)  # Sleep for 10 minutes before the next update

        except AttributeError:
            print("Table not found. Check the website structure.")
            return {"error": "Table not found. Check the website structure."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
