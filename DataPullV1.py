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
    soup = BeautifulSoup(response.content,"Htlml.parser")
    return soup

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)