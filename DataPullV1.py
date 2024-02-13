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

@app.get('/')
def earthquake():
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    response = re.get(url)
    
    # Check if the response status code is OK
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        # Return the HTML content of the page
        return str(soup)
    else:
        # If there's an error fetching the page, return an error message
        return {"error": "Failed to fetch earthquake data"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)
