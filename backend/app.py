import os
import json
from datetime import datetime as dt

from flask import Flask, request, jsonify
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.json
    name = data.get("name", "")
    date_str = data.get("date", "")
    time_str = data.get("time", "")
    place = data.get("place", "")

    # Геолокація
    geolocator = Nominatim(user_agent="astro_app")
    location_obj = geolocator.geocode(place)
    if not location_obj:
        return jsonify({"error": "Place not found"}), 400

    lat, lon = location_obj.latitude, location_obj.longitude
    location = GeoPos(lat, lon)

    # Часова зона
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=lat, lng=lon)
    timezone = pytz.timezone(tz_str)

    dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_obj = timezone.localize(dt_obj)
    date = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz_str)

    # Створення натальної карти з Placidus
    chart = Chart(date, location, hsys="PLACIDUS")

    # Тут можна збирати аспекти
    aspect_list = []  # залишаємо порожнім для прикладу

    # Збереження картинки
    key = f"{name}_{date_str}_{time_str}".replace(" ", "_")
    chart_path = os.path.join(CACHE_DIR, f"{key}.png")

    fig, ax = plt.subplots(figsize=(6,6))
    ax.text(0.5, 0.5, f"{name}", ha="center", va="center")  # простий логотип/текст
    try:
        plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)

    # Підготовка JSON
    chart_url = f"/cache/{key}.png"
    out = {
        "name": name,
        "date": date_str,
        "time": time_str,
        "place": place,
        "timezone": tz_str,
        "aspects_json": aspect_list,
        "chart_url": chart_url
    }

    json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(json_cache_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return jsonify(out)

@app.route("/cache/<filename>")
def cached_file(filename):
    return app.send_static_file(os.path.join(CACHE_DIR, filename))

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)