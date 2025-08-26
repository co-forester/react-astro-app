from flask import Flask, request, jsonify
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import matplotlib.pyplot as plt
import os
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
import math
import pytz

app = Flask(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

def get_planet_positions(chart):
    positions = {}
    for obj in const.PLANETS:
        body = chart.get(obj)
        positions[obj] = float(body.lon)
    return positions

def draw_chart(planet_positions, place):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis("off")

    circle = plt.Circle((0, 0), 1, fill=False, linewidth=2)
    ax.add_artist(circle)

    signs = const.SIGNS
    for i, sign in enumerate(signs):
        angle = math.radians(i * 30)
        x = 1.05 * math.cos(angle)
        y = 1.05 * math.sin(angle)
        ax.text(x, y, sign, ha="center", va="center", fontsize=10, fontweight="bold")

    for planet, lon in planet_positions.items():
        angle = math.radians(lon)
        x = 0.9 * math.cos(angle)
        y = 0.9 * math.sin(angle)
        ax.plot(x, y, 'o', markersize=10, label=planet)
        ax.text(x, y, planet, fontsize=9, ha="center", va="center")

    ax.legend(loc="upper right", fontsize=8)
    ax.text(0, -1.1, f"Натальна карта — {place}", ha="center", va="center", fontsize=12, fontweight="bold")

    chart_file = os.path.join(STATIC_FOLDER, "chart.png")
    fig.savefig(chart_file, bbox_inches="tight")
    plt.close(fig)
    return chart_file

@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        date_str = data.get("date")
        time_str = data.get("time")
        place_str = data.get("place")

        # Геокодинг
        location = geolocator.geocode(place_str)
        if not location:
            return jsonify({"error": f"Місто '{place_str}' не знайдено", "chart_image_url": "/static/chart.png", "status": "stub"}), 400
        lat, lon = location.latitude, location.longitude
        geopos = GeoPos(float(lat), float(lon))

        # Часовий пояс
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_name = "UTC"

        tz_offset_hours = timedelta(seconds=pytz.timezone(tz_name).utcoffset(datetime.utcnow()).total_seconds()).total_seconds()/3600

        # Парсимо дату та час
        day, month, year = map(int, date_str.split('.'))
        hour, minute = map(int, time_str.split(':'))

        # Локальний час -> UTC
        local_dt = datetime(year, month, day, hour, minute)
        utc_dt = local_dt - timedelta(hours=tz_offset_hours)

        # Правильний виклик Datetime
        dt = Datetime(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)

        # Створюємо натальну карту
        chart = Chart(dt, geopos)

        planet_positions = get_planet_positions(chart)
        chart_file = draw_chart(planet_positions, place_str)

        return jsonify({
            "chart_image_url": "/static/chart.png",
            "error": None,
            "status": "ok"
        })

    except Exception as e:
        return jsonify({"chart_image_url": "/static/chart.png", "error": str(e), "status": "stub"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)