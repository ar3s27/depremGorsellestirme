import requests
import folium

def fetch_earthquake_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch earthquake data:", response.status_code)
        return None

def create_map_with_markers(data):
    # Initialize the map
    harita = folium.Map(location=[39.3335, 35.1500], zoom_start=6)

    # Get the most recent earthquake data
    most_recent_quake = None
    most_recent_date = ""
    for quake_id, entry in data.items():
        date = entry['date']
        if date > most_recent_date:
            most_recent_date = date
            most_recent_quake = entry

    # Iterate over each earthquake event in the data
    for quake_id, entry in data.items():
        enlem = float(entry['latitude'])
        boylam = float(entry['longitude'])
        buyukluk = entry['magnitude']
        lokasyon = entry['location']

        # Create popup content for the marker
        popup_content = f"Lokasyon: {lokasyon}<br>Enlem: {enlem}<br>Boylam: {boylam}<br>Büyüklük: {buyukluk}<br>Tarih: {date}"

        # Determine marker color based on whether it is the most recent earthquake
        if entry == most_recent_quake:
            marker_color = 'red'  # You can choose any color you prefer for the most recent earthquake marker
        else:
            marker_color = 'blue'

        # Add marker to the map
        folium.Marker([enlem, boylam], popup=popup_content, icon=folium.Icon(color=marker_color)).add_to(harita)

    return harita

# URL for earthquake data
url = "https://deprem-gorsellestirme.vercel.app"

# Fetch earthquake data
earthquake_data = fetch_earthquake_data(url)

if earthquake_data:
    # Create the map with markers
    map_with_markers = create_map_with_markers(earthquake_data)

    # Save the map as an HTML file
    map_with_markers.save("earthquake_map.html")

    # Open the HTML file in the default web browser
    import webbrowser
    webbrowser.open("earthquake_map.html")