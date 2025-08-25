from flask import Flask, request, jsonify
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import matplotlib.pyplot as plt
import os
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import math

app = Flask(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

# Функція для координат планет на колі
def get_planet_positions(chart):
    positions = {}
    for obj in const.PLANETS:
        body = chart.get(obj)
        positions[obj] = float(body.lon)
    return positions

# Малюємо коло натальної карти
def draw_chart(planet_positions, place):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis("off")

    # Малюємо коло
    circle = plt.Circle((0, 0), 1, fill=False, linewidth=2)
    ax.add_artist(circle)

    # Додаємо знаки з 30° на коло
    signs = const.SIGNS
    for i, sign in enumerate(signs):
        angle = math.radians(i * 30)
        x = 1.05 * math.cos(angle)
        y = 1.05 * math.sin(angle)
        ax.text(x, y, sign, ha="center", va="center", fontsize=10, fontweight="bold")

    # Малюємо планети
    for planet, lon in planet_positions.items():
        angle = math.radians(lon)
        x = 0.9 * math.cos(angle)
        y = 0.9 * math.sin(angle)
        ax.plot(x, y, 'o', markersize=10, label=planet)
        ax.text(x, y, planet, fontsize=9, ha="center", va="center")

    # Легенда
    ax.legend(loc="upper right", fontsize=8)

    # Підпис
    ax.text(0, -1.1, f"Натальна карта — {place}", ha="center", va="center", fontsize=12, fontweight="bold")

    # Зберігаємо
    chart_file = os.path.join(STATIC_FOLDER, "chart.png")
    fig.savefig(chart_file, bbox_inches="tight")
    plt.close(fig)
    return chart_file

@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        date = data.get("date")
        time = data.get("time")
        place = data.get("place")

        # Отримуємо геопозицію міста
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": f"Місто '{place}' не знайдено", "status": "stub"}), 400

        lat, lon = location.latitude, location.longitude
        geopos = GeoPos(str(lat), str(lon))

        # Визначаємо часовий пояс
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_name = "UTC"
        tz = pytz.timezone(tz_name)

        # Парсимо дату і час
        naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        aware_dt = tz.localize(naive_dt)
        dt = Datetime(aware_dt.strftime("%Y-%m-%d %H:%M"), tz_name)

        # Створюємо натальну карту
        chart = Chart(dt, geopos)

        # Отримуємо позиції планет
        planet_positions = get_planet_positions(chart)

        # Малюємо картинку
        chart_file = draw_chart(planet_positions, place)

        return jsonify({"chart_image_url": "/static/chart.png", "error": None, "status": "ok"})

    except Exception as e:
        return jsonify({"chart_image_url": "/static/chart.png", "error": str(e), "status": "stub"}), 500

if __name__ == "__main__":
    app.run(debug=True)