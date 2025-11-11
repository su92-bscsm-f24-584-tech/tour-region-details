import requests
from flask import Flask,request,jsonify, render_template
from dotenv import load_dotenv
import os

load_dotenv()  # <- must come first
#OPENWEATHER_KEY = "37591d02f2f6d5bffd3b39df351e3555"
#OPENTRIPMAP_KEY = "bd2763877df34e9981feabfb6f89b1e6"

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
GOOGLE_API_KEY = os.getenv("OPENTRIPMAP_KEY")


app = Flask(__name__)


def top(lat, lon, radius=3000, max_places=10):
    """
    Fetch nearby landmarks using Google Places API.
    Returns a list of dictionaries with name, lat, lon, image.
    """
    places = []

    # Nearby Search endpoint
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": GOOGLE_API_KEY,
        "location": f"{lat},{lon}",
        "radius": radius,
        "type": "tourist_attraction"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return places

    data = response.json()
    results = data.get("results", [])[:max_places]

    for place in results:
        name = place.get("name")
        loc = place.get("geometry", {}).get("location", {})
        photo_ref = place.get("photos", [{}])[0].get("photo_reference")
        image_url = None

        if photo_ref:
            # Google Places Photo API
            image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=150&photoreference={photo_ref}&key={GOOGLE_API_KEY}"
        else:
            image_url = "https://via.placeholder.com/150x100?text=No+Image"

        if name and loc.get("lat") is not None and loc.get("lng") is not None:
            places.append({
                "name": name,
                "lat": loc["lat"],
                "lon": loc["lng"],
                "image": image_url
            })

    return places

def weather(city):
    city = city.strip()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code != 200:
        return None, None, None  # weather, places, city coords

    data = response.json()

    geocode_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_KEY}"
    geo_response = requests.get(geocode_url).json()
    if not geo_response:
        return None, None, None

    lat = geo_response[0]['lat']
    lon = geo_response[0]['lon']
    places = top(lat, lon)

    return f"{data['weather'][0]['description'].title()}, {data['main']['temp']}°C", places, (lat, lon)

@app.route("/")
def home():
    return render_template("index.html")
@app.route('/city-info')
def city_info():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "City name is required"}), 400

    weather_info, places, coords = weather(city)
    if not weather_info:
        return jsonify({"error": "City not found"}), 404

    return jsonify({
        "city": city,
        "weather": weather_info,
        "lat": coords[0],
        "lon": coords[1],
        "places": places
    })
if __name__=="__main__":
    app.run(debug=True)