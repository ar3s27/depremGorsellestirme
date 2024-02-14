import folium
import webbrowser

def create_map_with_markers(data):
    # Initialize the map
    harita = folium.Map(location=[39.9334, 32.8597], zoom_start=6)

    # Iterate over each earthquake event in the data
    for quake_id, entry in data.items():
        enlem = float(entry['latitude'])
        boylam = float(entry['longitude'])
        buyukluk = entry['magnitude']
        lokasyon = entry['location']

        # Create popup content for the marker
        popup_content = f"Lokasyon: {lokasyon}<br>Enlem: {enlem}<br>Boylam: {boylam}<br>Büyüklük: {buyukluk}"

        # Add marker to the map
        folium.Marker([enlem, boylam], popup=popup_content).add_to(harita)

    return harita

# Example JSON data
data = {
    "00cb5f04-853d-40d1-a0d1-fba58389a649": {"quake_id": "00cb5f04-853d-40d1-a0d1-fba58389a649", "location": "Yeşilyurt (Malatya)", "latitude": "38.14194", "longitude": "38.17222", "depth": "6.92", "magnitude": "2.3", "date": "2024-02-15 00:52:11"},
    "425bf1cb-f8da-4c4b-a1f0-2470d4f41285": {"quake_id": "425bf1cb-f8da-4c4b-a1f0-2470d4f41285", "location": "Doğanşehir (Malatya)", "latitude": "38.16833", "longitude": "37.77639", "depth": "7.0", "magnitude": "1.6", "date": "2024-02-15 00:25:34"},
    # Add more earthquake data here if needed
}

# Create the map with markers
map_with_markers = create_map_with_markers(data)

# Save the map as an HTML file
map_with_markers.save("earthquake_map.html")

# Open the HTML file in the default web browser
webbrowser.open("earthquake_map.html")
