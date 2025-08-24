import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime as dt

# --- Конфіг ---
STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

app = Flask(__name__, static_folder=STATIC_FOLDER)
CORS(app)


@app.route('/')
def index():
    return "🔮 Astro API працює! Використовуйте /generate для побудови натальної карти."


@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not (date and time and place):
        return jsonify({
            'chart_image_url': None,
            'status': 'error',
            'error': 'Введіть дату, час та місце'
        }), 400

    chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
    status = "ok"
    error_msg = None

    try:
        # --- Геолокація ---
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if not location:
            raise ValueError("Місце не знайдено")

        lat, lon = location.latitude, location.longitude

        # --- Часовий пояс ---
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        if not tz_name:
            tz_name = "UTC"
        tz = pytz.timezone(tz_name)

        # --- Парсинг дати й часу ---
        dt_obj = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(dt_obj)
        utc_dt = local_dt.astimezone(pytz.utc)

        fdate = utc_dt.strftime("%Y/%m/%d")
        ftime = utc_dt.strftime("%H:%M")
        pos = GeoPos(lat, lon)

        # --- Побудова карти через Flatlib ---
        chart = Chart(Datetime(fdate, ftime, "+00:00"), pos)

        # --- Малювання карти ---
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Натальна карта: {place}", fontsize=14)

        for obj in chart.objects:
            ax.plot([0], [0], 'o', label=f"{obj} {chart[obj].lon:.2f}°")

        ax.legend()
        plt.savefig(chart_path)
        plt.close(fig)

    except Exception as e:
        print("Помилка генерації карти:", e)
        status = "stub"
        error_msg = str(e)
        # --- Якщо є помилка → генеруємо заглушку ---
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.text(
            0.5, 0.5,
            f"Натальна карта\n{place}\n(заглушка)",
            ha='center', va='center', fontsize=14
        )
        plt.savefig(chart_path)
        plt.close(fig)

    return jsonify({
        'chart_image_url': f'/static/chart.png',
        'status': status,
        'error': error_msg
    }), 200


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)