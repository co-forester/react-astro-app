import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.const import SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, ASC, MC
# from flatlib.object import DEFAULT_IDS
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
import io
import math
from datetime import datetime as dt
import pytz
from timezonefinder import TimezoneFinder

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.50.16:3000",
    "https://your-prod-domain.com"
])

# Буфер для збереження зображення
chart_image_buffer = io.BytesIO()

@app.route('/generate', methods=['POST'])
def generate_chart():
    global chart_image_buffer

    data = request.json
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not (date and time and place):
        return jsonify({'error': 'Неповні дані'}), 400

    try:
        # Геолокація
        geolocator = Nominatim(user_agent="astrology-app")
        location = geolocator.geocode(place)

        if not location:
            print(f"[WARN] Місце '{place}' не знайдено. Використовується Київ.")
            location = type("Geo", (), {})()
            location.latitude = 50.4501
            location.longitude = 30.5234
            timezone_str = 'Europe/Kyiv'
        else:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            if not timezone_str:
                timezone_str = 'Europe/Kyiv'

        local_tz = pytz.timezone(timezone_str)
        naive_dt = dt.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        localized_dt = local_tz.localize(naive_dt)
        offset_minutes = localized_dt.utcoffset().total_seconds() / 60
        offset_hours = offset_minutes / 60
        offset_str = f"{int(offset_hours)}:00"

        dt_flatlib = Datetime(date.replace('-', '/'), time, offset_str)
        pos = GeoPos(location.latitude, location.longitude)
        objects = [SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, ASC, MC]
        chart = Chart(date, pos, IDs=objects)
        # Побудова зображення
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('S')
        radius = 1
        ax.set_rlim(0, 1.5)
        ax.grid(True)

        circle = plt.Circle((0, 0), radius, transform=ax.transData._b, fill=False, color='black')
        ax.add_artist(circle)

        object_data = []

        for obj in chart.objects:
            lon_deg = obj.lon
            theta = math.radians(lon_deg)
            ax.plot(theta, radius, 'o', color='blue')
            ax.text(theta, radius + 0.1, obj.id, ha='center', va='center', fontsize=8)
            object_data.append({
                'id': obj.id,
                'sign': obj.sign,
                'lon': round(obj.lon, 2),
                'lat': round(obj.lat, 2),
                'speed': round(obj.speed, 2)
            })

        ax.set_axis_off()

        chart_image_buffer = io.BytesIO()
        plt.savefig(chart_image_buffer, format='png', bbox_inches='tight', transparent=True)
        chart_image_buffer.seek(0)
        plt.close()

        print("[INFO] Карту збережено у буфер памʼяті.")

        return jsonify({
            'status': 'success',
            'place': place,
            'latitude': round(location.latitude, 4),
            'longitude': round(location.longitude, 4),
            'timezone': timezone_str,
            'utc_offset': offset_str,
            'objects': object_data,
            'chart_image_url': '/chart.png'
        })

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chart.png')
def get_chart_image():
    global chart_image_buffer
    if chart_image_buffer:
        chart_image_buffer.seek(0)
        return send_file(chart_image_buffer, mimetype='image/png')
    else:
        return jsonify({'error': 'Карта ще не створена'}), 404

if __name__ == '__main__':
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)