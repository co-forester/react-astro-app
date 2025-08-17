from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import matplotlib.pyplot as plt
import math
import os
import pytz

app = Flask(__name__)
CORS(app)

CHART_PATH = '/app/chart.png'

# Кольори для знаків зодіаку
SIGN_COLORS = {
    'Aries': '#FF0000', 'Taurus': '#008000', 'Gemini': '#FFFF00', 'Cancer': '#00FFFF',
    'Leo': '#FFA500', 'Virgo': '#808080', 'Libra': '#FFC0CB', 'Scorpio': '#800000',
    'Sagittarius': '#0000FF', 'Capricorn': '#000000', 'Aquarius': '#00FF00', 'Pisces': '#800080'
}

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Невірні дані'}), 400

    date = data.get('date')   # формат YYYY-MM-DD
    time = data.get('time')   # формат HH:MM
    place = data.get('place')

    if not date or not time or not place:
        return jsonify({'error': 'Невірні дані'}), 400

    try:
        # Розбираємо дату і час
        year, month, day = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))

        # Геокодування
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if not location:
            return jsonify({'error': 'Місце не знайдено'}), 400

        lat, lon = location.latitude, location.longitude

        # Часовий пояс
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_name = "UTC"

        # Створюємо chart
        dt = Datetime(f"{year}/{month:02d}/{day:02d}",
                      f"{hour:02d}:{minute:02d}",
                      tz_name)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos, IDs=const.LIST_OBJECTS)

        object_data = []
        for obj in chart.objects:
            object_data.append({
                'id': obj.id,
                'sign': obj.sign,
                'lon': round(obj.lon, 2),
                'lat': round(obj.lat, 2),
                'speed': round(obj.ecl_lon_speed, 2)
            })

        # Малюємо натальну карту
        plt.figure(figsize=(6, 6))
        ax = plt.gca()
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect('equal')
        plt.axis('off')

        # Коло зодіаку
        circle = plt.Circle((0, 0), 1, color='lightgrey', fill=False, linewidth=2)
        ax.add_artist(circle)

        # Сектори 12 будинків і підписи
        for i in range(12):
            angle_deg = i * 30
            angle_rad = math.radians(angle_deg)
            x = math.cos(angle_rad)
            y = math.sin(angle_rad)
            plt.plot([0, x], [0, y], color='grey', linewidth=1)
            hx = 0.7 * math.cos(angle_rad + math.radians(15))
            hy = 0.7 * math.sin(angle_rad + math.radians(15))
            plt.text(hx, hy, str(i+1), fontsize=10, ha='center', va='center', fontweight='bold')

        # Внутрішнє коло будинків
        inner_circle = plt.Circle((0, 0), 0.7, color='lightgrey', fill=False, linestyle='dashed', linewidth=1)
        ax.add_artist(inner_circle)

        # Планети
        for obj in chart.objects:
            sign_color = SIGN_COLORS.get(obj.sign, '#000000')
            angle = math.radians(obj.lon)
            radius = 0.95
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            plt.plot(x, y, 'o', color=sign_color, markersize=10)
            plt.text(x*1.05, y*1.05, obj.id, fontsize=8, ha='center', va='center')

        # Легенда
        for sign, color in SIGN_COLORS.items():
            ax.plot([], [], 'o', color=color, label=sign)
        plt.legend(loc='upper right', fontsize=6)

        plt.title(f'Natal Chart for {date} {time} ({place})', fontsize=10)
        plt.savefig(CHART_PATH, bbox_inches='tight')
        plt.close()

        return jsonify({
            'objects': object_data,
            'chart': '/chart.png'
        })

    except Exception as e:
        return jsonify({'error': str(e), 'trace': repr(e)}), 500


@app.route('/chart.png', methods=['GET'])
def chart_png():
    if os.path.exists(CHART_PATH):
        return send_file(CHART_PATH, mimetype='image/png')
    return jsonify({'error': 'Chart not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)