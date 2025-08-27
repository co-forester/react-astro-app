import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects

app = Flask(__name__)
CORS(app)

# --------- Функція для геокодування ----------
def geocode_place(place: str):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place)
    if location:
        return location.latitude, location.longitude
    return 50.45, 30.523  # fallback Київ

# --------- Генерація карти ----------
@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.get_json()
    date = data.get("date")   # формат YYYY-MM-DD
    time = data.get("time")   # формат HH:MM
    place = data.get("place")

    # Геолокація
    lat, lon = geocode_place(place)

    # Часовий пояс
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if timezone_str is None:
        timezone_str = "UTC"
    tz = pytz.timezone(timezone_str)

    # Формування flatlib datetime
    naive_dt = dt.strptime(date + " " + time, "%Y-%m-%d %H:%M")
    aware_dt = tz.localize(naive_dt)
    fdate = Datetime(
        aware_dt.strftime("%Y/%m/%d"),
        aware_dt.strftime("%H:%M"),
        aware_dt.utcoffset().total_seconds() / 3600
    )

    pos = GeoPos(lat, lon)
    chart = Chart(fdate, pos)

    # --- Побудова графіка ---
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis("off")

    # Коло
    circle = plt.Circle((0, 0), 0.9, fill=False, color="black")
    ax.add_artist(circle)

    # Планети
    planets = chart.objects
    for obj in planets:
        angle = math.radians(obj.lon)
        x = 0.8 * math.cos(angle)
        y = 0.8 * math.sin(angle)
        ax.plot(x, y, "o", label=obj)
        ax.text(x, y, obj, fontsize=8, ha="center", va="center")

    # Збереження
    output_path = os.path.join(os.getcwd(), "chart.png")
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

    return jsonify({
        "message": "Chart generated successfully",
        "chart_url": "/chart.png"
    })

# --------- Віддача збереженого файлу ----------
@app.route("/chart.png")
def get_chart():
    return send_from_directory(os.getcwd(), "chart.png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)