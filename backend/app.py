import os
import io
import math
import uuid
import traceback
import tempfile
from datetime import datetime as dt
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.const import SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, ASC, MC
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import matplotlib.pyplot as plt
import swisseph as swe

# --- Шлях до ефемерид на Fly.io ---
EPHE_PATH = "/data/ephe"
os.makedirs(EPHE_PATH, exist_ok=True)

# --- Перевірка ефемерид ---
if os.listdir(EPHE_PATH):
    print(f"Ефемериди знайдено у {EPHE_PATH}")
else:
    print(f"Увага: ефемериди не знайдено у {EPHE_PATH}. Натальні карти не будуть створюватися.")

# --- Налаштування swisseph ---
swe.set_ephe_path(EPHE_PATH)

# --- Flask ---
app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://react-astro-app.vercel.app",
    "https://albireo-daria-96.fly.dev"
])

@app.route('/generate', methods=['POST'])
def generate_chart():
    if not os.listdir(EPHE_PATH):
        return jsonify({'error': 'Ефемериди відсутні на сервері'}), 500

    data = request.json
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not (date and time and place):
        return jsonify({'error': 'Неповні дані'}), 400

    try:
        # --- Геолокація ---
        geolocator = Nominatim(user_agent="astrology-app")
        location = geolocator.geocode(place, timeout=10)
        if not location:
            location = type("Geo", (), {})()
            location.latitude = 50.4501
            location.longitude = 30.5234
            timezone_str = 'Europe/Kyiv'
        else:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            if not timezone_str:
                timezone_str = 'Europe/Kyiv'

        # --- Локалізований час ---
        local_tz = pytz.timezone(timezone_str)
        naive_dt = dt.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        localized_dt = local_tz.localize(naive_dt)
        offset_hours = localized_dt.utcoffset().total_seconds() / 3600
        offset_str = f"{int(offset_hours)}:{int((offset_hours % 1) * 60):02d}"

        dt_flatlib = Datetime(date.replace('-', '/'), time, offset_str)
        pos = GeoPos(location.latitude, location.longitude)
        objects = [SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, ASC, MC]

        chart = Chart(dt_flatlib, pos, ids=objects)

        # --- Побудова картинки ---
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')
        ax.set_rlim(0, 1.5)
        ax.grid(True)
        ax.set_axis_off()

        object_data = []
        for obj in chart.objects:
            theta = math.radians(obj.lon)
            ax.plot(theta, 1, 'o', color='blue')
            ax.text(theta, 1.1, obj.id, ha='center', va='center', fontsize=8)
            object_data.append({
                'id': obj.id,
                'sign': obj.sign,
                'lon': round(obj.lon, 2),
                'lat': round(obj.lat, 2),
                'speed': round(obj.speed, 2)
            })

        # --- Тимчасовий файл для картинки ---
        tmp_dir = tempfile.gettempdir()
        tmp_filename = os.path.join(tmp_dir, f"chart_{uuid.uuid4().hex}.png")
        plt.savefig(tmp_filename, format='png', bbox_inches='tight', transparent=True)
        plt.close()

        return jsonify({
            'status': 'success',
            'place': place,
            'latitude': round(location.latitude, 4),
            'longitude': round(location.longitude, 4),
            'timezone': timezone_str,
            'utc_offset': offset_str,
            'objects': object_data,
            'chart_image_url': f'/chart/{os.path.basename(tmp_filename)}'
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/chart/<filename>')
def get_chart_image(filename):
    tmp_dir = tempfile.gettempdir()
    filepath = os.path.join(tmp_dir, filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    else:
        return jsonify({'error': 'Карта ще не створена'}), 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)