# app.py

import os
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless режим
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        name = data.get("name", "Person")
        date_str = data.get("date")   # YYYY-MM-DD
        time_str = data.get("time")   # HH:MM
        place = data.get("place")     # Місто/адреса

        # Геолокація
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400

        lat, lon = location.latitude, location.longitude

        # Таймзона
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        if not tz_str:
            tz_str = "UTC"

        tz = pytz.timezone(tz_str)

        # Локальний час
        naive_dt = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive_dt)

        # Flatlib datetime
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"),
                         local_dt.strftime("%H:%M"),
                         tz_str)
        pos = GeoPos(lat, lon)
        chart = Chart(fdate, pos)

        # Малюємо PNG
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Natal Chart - {name}")
        ax.plot([0, 1], [0, 1], "o")  # простий маркер
        ax.axis("off")

        os.makedirs("static", exist_ok=True)
        chart_path = os.path.join("static", "chart.png")
        plt.savefig(chart_path, bbox_inches="tight")
        plt.close(fig)

        return jsonify({
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "chart_url": "/chart.png"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chart.png")
def get_chart():
    return send_from_directory("static", "chart.png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)