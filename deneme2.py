from fastapi import FastAPI
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import time
from selenium import webdriver
import uvicorn

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

earthquake_info = {}
@app.get('/')
def earthquake():
    while True:
        url = "https://deprem.afad.gov.tr/last-earthquakes.html"
        driver = webdriver.Chrome()
        driver.get(url)
        time.sleep(5)

        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, "html.parser")

        try:
            table = soup.find("table", class_="k-grid-table")
            tbody = table.find("tbody", kendogridtablebody="")
            rows = tbody.find_all("tr")

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

                    if quake_id in earthquake_info:
                        continue
                    else:
                        print("Yer: " + location)
                        print("Enlem: " + latitude)
                        print("Boylam: " + longitude)
                        print("Derinlik: " + depth)
                        print("Büyüklük: " + magnitude)
                        print("Tarih: " + date)
                        print("\n")

                        earthquake_info[quake_id] = {
                            'quake_id': quake_id,
                            "location": location,
                            "latitude": latitude,
                            "longitude": longitude,
                            "depth": depth,
                            "magnitude": magnitude,
                            "date": date
                        }
            
            return earthquake_info

        except AttributeError:
            print("Table not found. Check the website structure.")
            return {"error": "Table not found. Check the website structure."}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7000)
