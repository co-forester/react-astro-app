#!/usr/bin/env python3
import math
import os
import json
from datetime import datetime
import pytz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

app = Flask(__name__)
CORS(app)

CHART_PATH = "chart.png"
FALLBACK_FILE = "fallback_coords.json"

SIGN_COLORS = {
    'Aries': '#FF0000', 'Taurus': '#FFA500', 'Gemini': '#FFFF00',
    'Cancer': '#008000', 'Leo': '#FFD700', 'Virgo': '#00FF00',
    'Libra': '#00FFFF', 'Scorpio': '#800080', 'Sagittarius': '#FF00FF',
    'Capricorn': '#A52A2A', 'Aquarius': '#0000FF', 'Pisces': '#FFC0CB'
}

# Завантаження бази fallback
if os.path.exists(FALLBACK_FILE):
    with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
        FALLBACK_COORDS = json.load(f)
else:
    FALLBACK_COORDS = {}

def get_coords(place: str):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place)
    if location:
        return location.latitude, location.longitude
    elif place in FALLBACK_COORDS:
        lat, lon = FALLBACK_COORDS[place]
        print(f"[FALLBACK] Використано координати з бази: {lat}, {lon}")
        return lat, lon
    else:
        # fallback: невідоме місто → ставимо (0,0)
        lat, lon = 0.0, 0.0
        FALLBACK_COORDS[place] = [lat, lon]
        with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(FALLBACK_COORDS, f, ensure_ascii=False, indent=2)
        print(f"[AUTO-FALLBACK] Місто '{place}' не знайдено, використано координати (0,0)")
        return lat, lon

def format_offset(dt_obj: datetime) -> str:
    total_minutes = int(dt_obj.utcoffset().total_seconds() // 60)
    hours = total_minutes // 60
    minutes = abs(total_minutes % 60)
    return f"{hours:+d}:{minutes:02d}"

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Невірні дані'}), 400

    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not date or not time or not place:
        return jsonify({'error': 'Невірні дані'}), 400

    try:
        year, month, day = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))

        lat, lon = get_coords(place)

        # часовий пояс
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        timezone = pytz.timezone(tz_name)
        dt_obj = datetime(year, month, day, hour, minute)
        dt_obj = timezone.localize(dt_obj)

        offset_str = format_offset(dt_obj)

        dt = Datetime(dt_obj.strftime("%Y/%m/%d"), dt_obj.strftime("%H:%M"), offset_str)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos, IDs=const.LIST_OBJECTS)

        object_data = [{
            'id': obj.id,
            'sign': obj.sign,
            'lon': round(obj.lon, 2),
            'lat': round(obj.lat, 2),
            'speed': round(obj.ecl_lon_speed, 2)
        } for obj in chart.objects]

        # Малювання карти
        plt.figure(figsize=(6, 6))
        ax = plt.gca()
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect('equal')
        plt.axis('off')

        ax.add_artist(plt.Circle((0, 0), 1, color='lightgrey', fill=False, linewidth=2))
        for i in range(12):
            angle = math.radians(i * 30)
            x, y = math.cos(angle), math.sin(angle)
            plt.plot([0, x], [0, y], color='grey', linewidth=1)
            hx, hy = 0.7 * math.cos(angle + math.radians(15)), 0.7 * math.sin(angle + math.radians(15))
            plt.text(hx, hy, str(i+1), fontsize=10, ha='center', va='center', fontweight='bold')
        ax.add_artist(plt.Circle((0, 0), 0.7, color='lightgrey', fill=False, linestyle='dashed', linewidth=1))

        for obj in chart.objects:
            color = SIGN_COLORS.get(obj.sign, '#000000')
            angle = math.radians(obj.lon)
            r = 0.95
            x, y = r * math.cos(angle), r * math.sin(angle)
            plt.plot(x, y, 'o', color=color, markersize=10)
            plt.text(x*1.05, y*1.05, obj.id, fontsize=8, ha='center', va='center')

        for sign, color in SIGN_COLORS.items():
            ax.plot([], [], 'o', color=color, label=sign)
        plt.legend(loc='upper right', fontsize=6)
        plt.title(f'Natal Chart for {date} {time} ({place})', fontsize=10)
        plt.savefig(CHART_PATH, bbox_inches='tight')
        plt.close()

        return jsonify({'objects': object_data, 'chart': '/chart.png'})

    except Exception as e:
        return jsonify({'error': str(e), 'trace': repr(e)}), 500

@app.route('/chart.png', methods=['GET'])
def get_chart():
    if os.path.exists(CHART_PATH):
        return send_file(CHART_PATH, mimetype='image/png')
    return jsonify({'error': 'Карта ще не створена'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)