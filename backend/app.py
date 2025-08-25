import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import matplotlib
matplotlib.use('Agg')  # бекенд без GUI
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
os.makedirs(STATIC_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_FOLDER)
CORS(app)


@app.route('/')
def index():
    return "🔮 Astro API працює! Використовуйте /generate для побудови натальної карти."


@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json or {}
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
        location = geolocator.geocode(place, timeout=10)
        if not location:
            raise ValueError("Місце не знайдено")

        lat, lon = location.latitude, location.longitude

        # --- Часовий пояс ---
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        tz = pytz.timezone(tz_name)

        # --- Парсинг дати й часу ---
        dt_obj = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(dt_obj)
        utc_dt = local_dt.astimezone(pytz.utc)

        fdate = utc_dt.strftime("%Y/%m/%d")
        ftime = utc_dt.strftime("%H:%M")
        pos = GeoPos(lat, lon)

               # --- Побудова карти ---
        chart = Chart(Datetime(fdate, ftime, "+00:00"), pos)

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Натальна карта: {place}", fontsize=14)

        for obj in chart.objects:
            planet = chart.get(obj)   # <-- ключова зміна
            ax.plot([0], [0], 'o', label=f"{obj} {planet.lon:.2f}°")

        ax.legend(fontsize=8, loc='upper left')
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close(fig)

    except Exception as e:
        print("Помилка генерації карти:", e)
        status = "stub"
        error_msg = str(e)
        # --- fallback-заглушка ---
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.text(
            0.5, 0.5,
            f"Натальна карта\n{place}\n(заглушка)",
            ha='center', va='center', fontsize=14
        )
        plt.axis("off")
        plt.savefig(chart_path)
        plt.close(fig)

    return jsonify({
        'chart_image_url': f'/static/chart.png',
        'status': status,
        'error': error_msg
    })


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

# Healthcheck для Fly
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Fly.io вимагає PORT з env
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)