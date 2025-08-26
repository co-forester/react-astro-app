from flask import Flask, request, jsonify
from flask_cors import CORS
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

app = Flask(__name__)
CORS(app)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

def create_datetime(date_str: str, time_str: str, tz_offset_hours: float = 3.0) -> Datetime:
    try:
        day, month, year = map(int, date_str.split('.'))
        hour, minute = map(int, time_str.split(':'))
        local_dt = datetime(year, month, day, hour, minute)
        utc_dt = local_dt - timedelta(hours=tz_offset_hours)
        dt = Datetime(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
        return dt
    except Exception as e:
        raise ValueError(f"Error creating Datetime: {str(e)}")

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
        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        date = data.get("date")
        time = data.get("time")
        place = data.get("place")

        # Отримуємо геопозицію
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": f"Місто '{place}' не знайдено", "status": "stub"}), 400
        lat, lon = location.latitude, location.longitude
        geopos = GeoPos(lat, lon)

        # Визначаємо часовий пояс
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        tz_offset_hours = 3.0  # дефолт +3, можна замінити на обчислений через pytz
        dt = create_datetime(date, time, tz_offset_hours)

        # Створюємо натальну карту
        chart = Chart(dt, geopos)

        # Отримуємо позиції планет
        planet_positions = get_planet_positions(chart)

        # Малюємо картинку
        chart_file = draw_chart(planet_positions, place)

        return jsonify({
            "firstName": first_name,
            "lastName": last_name,
            "date": date,
            "time": time,
            "place": place,
            "chart_image_url": "/static/chart.png",
            "error": None,
            "status": "ok"
        })

    except Exception as e:
        return jsonify({
            "chart_image_url": "/static/chart.png",
            "error": str(e),
            "status": "stub"
        }), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)