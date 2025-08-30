import os
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
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

app = Flask(__name__)
CORS(app)

# ----------------------
# Хелсі-ендпоінт
# ----------------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------------
# Генерація натальної карти
# ----------------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    try:
        date_str = data.get("date")  # формат YYYY-MM-DD
        time_str = data.get("time")  # формат HH:MM
        city = data.get("city")

        if not all([date_str, time_str, city]):
            return jsonify({"error": "date, time та city обов'язкові"}), 400

        dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        # ----------------------
        # Геокодування
        # ----------------------
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(city, timeout=10)
        if not location:
            return jsonify({"error": f"Не знайдено місто {city}"}), 404

        latitude, longitude = location.latitude, location.longitude

        # ----------------------
        # Часовий пояс
        # ----------------------
        tz = pytz.timezone(TimezoneFinder().timezone_at(lng=longitude, lat=latitude))
        dt_obj = tz.localize(dt_obj)

        # ----------------------
        # Flatlib datetime та позиція
        # ----------------------
        astro_dt = Datetime(dt_obj.day, dt_obj.month, dt_obj.year,
                            dt_obj.hour, dt_obj.minute, tz.zone)
        pos = GeoPos(latitude, longitude)

        # ----------------------
        # Створення карти Placidus
        # ----------------------
        chart = Chart(astro_dt, pos, hsys="P")  # Placidus

        # ----------------------
        # Малюємо карту
        # ----------------------
        fig, ax = plt.subplots(figsize=(6,6))
        ax.set_title(f"Натальна карта: {city} {date_str} {time_str}")
        ax.axis("off")
        # Тут можна додати кастомізацію: кола, логотипи, аспекти, сектори домов
        plt.savefig("chart.png")
        plt.close(fig)

        return jsonify({
            "message": "Натальна карта згенерована",
            "chart_url": "/chart.png"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------
# Віддаємо зображення карти
# ----------------------
@app.route("/chart.png")
def chart_png():
    return send_from_directory(os.getcwd(), "chart.png")

# ----------------------
# Запуск сервера
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)