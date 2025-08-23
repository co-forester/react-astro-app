from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

app = Flask(__name__)
CORS(app)

STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

geolocator = Nominatim(user_agent="albireo_app")
tf = TimezoneFinder()

# ====================== Малювання аспектів ======================
def check_aspect(p1_lon, p2_lon, orb=6):
    aspects = {
        'conj': 0,
        'opp': 180,
        'tri': 120,
        'sq': 90,
        'sex': 60
    }
    aspect_list = []
    for key, angle in aspects.items():
        diff = abs(p1_lon - p2_lon) % 360
        diff = min(diff, 360 - diff)
        if diff <= orb:
            aspect_list.append(key)
    return aspect_list

aspect_colors = {
    'conj': 'red',
    'opp': 'blue',
    'tri': 'green',
    'sq': 'orange',
    'sex': 'purple'
}

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not (date and time and place):
        return jsonify({'error': 'Введіть дату, час та місце'}), 400

    # Геокодування
    location = geolocator.geocode(place)
    if not location:
        return jsonify({'error': 'Не вдалося знайти координати міста'}), 400

    lat, lon = location.latitude, location.longitude

    # Визначення часового поясу
    tz_str = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
    tz = pytz.timezone(tz_str)

    # Локалізація дати і часу
    dt_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    dt_local = tz.localize(dt_naive)
    dt = Datetime(
        dt_local.strftime("%Y/%m/%d"),
        dt_local.strftime("%H:%M"),
        dt_local.strftime("%z")
    )

    geo = GeoPos(lat, lon)

    # Класична натальна карта
    objects = [const.SUN, const.MOON, const.MERCURY, const.VENUS,
               const.MARS, const.JUPITER, const.SATURN, const.URANUS,
               const.NEPTUNE, const.PLUTO]
    chart = Chart(dt, geo, objects=objects)

    # ====================== Малювання карти ======================
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.1,1.1)
    ax.set_ylim(-1.1,1.1)
    ax.set_aspect('equal')
    ax.axis('off')

    # Коло для натальної карти
    circle = plt.Circle((0,0),1, color='black', fill=False, linewidth=2)
    ax.add_artist(circle)

    # Логотип у центрі
    ax.text(0, 0, "Albireo Daria", ha='center', va='center', fontsize=16, fontweight='bold', color='purple')

    # Розміщення планет
    for obj in chart.objects:
        x = np.cos(np.radians(obj.lon))
        y = np.sin(np.radians(obj.lon))
        ax.plot(x, y, 'o', color='blue', markersize=10)
        ax.text(x*1.1, y*1.1, obj.id, ha='center', va='center', fontsize=10, color='black')

    # Малювання аспектів
    planets = chart.objects
    for i in range(len(planets)):
        for j in range(i+1, len(planets)):
            p1 = planets[i]
            p2 = planets[j]
            aspect_types = check_aspect(p1.lon, p2.lon)
            x1, y1 = np.cos(np.radians(p1.lon)), np.sin(np.radians(p1.lon))
            x2, y2 = np.cos(np.radians(p2.lon)), np.sin(np.radians(p2.lon))
            for aspect_type in aspect_types:
                ax.plot([x1, x2], [y1, y2], color=aspect_colors.get(aspect_type,'gray'), linewidth=1.5, alpha=0.7)

    chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
    plt.savefig(chart_path, bbox_inches='tight', dpi=150)
    plt.close(fig)

    return jsonify({'chart_image_url': f'/static/chart.png'}), 200

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)