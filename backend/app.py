import os
import io
import math
import traceback
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.const import SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, ASC, MC
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import matplotlib.pyplot as plt
import pytz
import pyswisseph as swe
import flatlib.core
import uuid

# Використання pyswisseph
flatlib.core.set_ephemeris('pyswisseph')
# Якщо у контейнері немає ефемерид, можна скопіювати у /app/ephe
swe.set_ephe_path('/app/ephe')

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.50.16:3000",
    "https://react-astro-app.vercel.app"
])


@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json
    date = data.get('date')  # формат 'YYYY-MM-DD'
    time = data.get('time')  # формат 'HH:MM'
    place = data.get('place')  # наприклад, 'Kyiv, Ukraine'

    if not (date and time and place):
        return jsonify({'error': 'Неповні дані'}), 400

    try:
        # Геолокація
        geolocator = Nominatim(user_agent="astrology-app")
        location = geolocator.geocode(place, timeout=10)

        if not location:
            # fallback
            location = type("Geo", (), {})()
            location.latitude = 50.4501
            location.longitude = 30.5234
            timezone_str = 'Europe/Kyiv'
        else:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            if not timezone_str:
                timezone_str = 'Europe/Kyiv'

        # Локалізований час
        local_tz = pytz.timezone(timezone_str)
        naive_dt = dt.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        localized_dt = local_tz.localize(naive_dt)
        offset_hours = localized_dt.utcoffset().total_seconds() / 3600
        offset_str = f"{int(offset_hours)}:{int((offset_hours % 1) * 60):02d}"

        # Flatlib datetime
        dt_flatlib = Datetime(date.replace('-', '/'), time, offset_str)
        pos = GeoPos(location.latitude, location.longitude)
        objects = [SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, ASC, MC]

        # Юліанська дата (для debug)
        jd_ut = swe.julday(localized_dt.year, localized_dt.month, localized_dt.day,
                           localized_dt.hour + localized_dt.minute / 60.0)

        # Побудова карти
        chart = Chart(dt_flatlib, pos, ids=objects)

        # Побудова картинки
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')  # нуль зверху
        ax.set_rlim(0, 1.5)
        ax.grid(True)
        ax.set_axis_off()
        circle = plt.Circle((0, 0), 1, transform=ax.transData._b, fill=False, color='black')
        ax.add_artist(circle)

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

        # Збереження тимчасової картинки
        tmp_filename = f"/tmp/chart_{uuid.uuid4().hex}.png"
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
    filepath = f"/tmp/{filename}"
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    else:
        return jsonify({'error': 'Карта ще не створена'}), 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)