import os
from datetime import datetime as dt
from flask import Flask, request, jsonify
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

app = Flask(__name__)
CORS(app)

# --- Система домів (Placidus) ---
HOUSES_SYSTEMS = {
    "PLACIDUS": "P",
    "KOCH": "K",
    "CAMPANUS": "C",
    "REGIOMONTAUS": "R",
    "EQUAL": "E",
    "PORPHYRY": "O",
    "TOPOCENTRIC": "T",
}

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tzname = tf.timezone_at(lat=lat, lng=lon)
    return pytz.timezone(tzname)

def create_chart(date_str, time_str, lat, lon, hsys_name="PLACIDUS"):
    tz = get_timezone(lat, lon)
    astro_dt = Datetime(date_str, time_str, tz.zone)
    pos = GeoPos(lat, lon)

    hsys = HOUSES_SYSTEMS.get(hsys_name.upper(), "P")  # Placidus як дефолт
    try:
        chart = Chart(astro_dt, pos, hsys=hsys)
    except Exception:
        chart = Chart(astro_dt, pos)  # fallback без домів
    return chart

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    try:
        date_str = data["date"]       # формат 'YYYY-MM-DD'
        time_str = data["time"]       # формат 'HH:MM'
        city = data["city"]
        hsys_name = data.get("hsys", "PLACIDUS")

        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(city, timeout=10)
        if not location:
            return jsonify({"error": f"Місто '{city}' не знайдено"}), 400

        chart = create_chart(date_str, time_str, location.latitude, location.longitude, hsys_name)

        # Тут твоя логіка створення картинки та JSON з аспектами
        # chart_image = ...
        # aspects_json = ...

        return jsonify({"message": "Chart створено успішно"})  # тимчасово
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)