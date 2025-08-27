import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory, Response
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

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()


def geocode_place(place):
    """Повертає координати та часовий пояс за назвою міста"""
    location = geolocator.geocode(place)
    if not location:
        return None, None, None
    latitude, longitude = location.latitude, location.longitude
    tz_name = tf.timezone_at(lng=longitude, lat=latitude)
    return latitude, longitude, tz_name


def generate_chart(date, time, place):
    """Генерує натальну карту і зберігає chart.png"""
    latitude, longitude, tz_name = geocode_place(place)
    if not tz_name:
        tz_name = "Europe/Kiev"  # fallback

    tz = pytz.timezone(tz_name)
    naive_dt = dt.strptime(date + " " + time, "%Y-%m-%d %H:%M")
    local_dt = tz.localize(naive_dt)

    fdt = Datetime(local_dt.strftime("%Y/%m/%d"),
                   local_dt.strftime("%H:%M"),
                   tz_name)
    pos = GeoPos(str(latitude), str(longitude))
    chart = Chart(fdt, pos)

    # малюємо просту карту
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")

    circle = plt.Circle((0, 0), 1, color="black", fill=False)
    ax.add_artist(circle)

    # планети
    for obj in chart.objects:
        lon = obj.lon
        x = math.cos(math.radians(lon))
        y = math.sin(math.radians(lon))
        ax.plot(x, y, "o", label=obj.body, markersize=8)
        ax.text(x * 1.1, y * 1.1, obj.body, fontsize=8, ha="center")

    ax.legend()
    plt.savefig("chart.png", dpi=150)
    plt.close(fig)

    return chart


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    date = data.get("date")
    time = data.get("time")
    place = data.get("place")

    chart = generate_chart(date, time, place)

    planets_data = {
        obj.body: {"lon": obj.lon, "lat": obj.lat, "sign": obj.sign}
        for obj in chart.objects
    }

    return jsonify({
        "planets": planets_data,
        "chart_url": "/chart.png"
    })


@app.route("/chart.png")
def get_chart():
    return send_from_directory(".", "chart.png", mimetype="image/png")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)