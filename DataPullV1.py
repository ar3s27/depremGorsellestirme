from fastapi import FastAPI
import uvicorn
import requests as re
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

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
    
    # Check if the response status code is OK
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        # Return the HTML content of the page
        table = soup.find("table")
        rows = table.find_all("tr")
        for row in rows[:11]:
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

                    kutuphane[quake_id] = {
                        'quake_id': quake_id,
                        "location": location,
                        "latitude": latitude,
                        "longitude": longitude,
                        "depth": depth,
                        "magnitude": magnitude,
                        "date": date}
        return kutuphane   
    else:
        # If there's an error fetching the page, return an error message
        return {"error": "Failed to fetch earthquake data"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)
