from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from datetime import datetime
import numpy as np

app = Flask(__name__)
CORS(app)

STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

geolocator = Nominatim(user_agent="albireo_app")
tf = TimezoneFinder()

# Кольори планет за стихіями
ELEMENT_COLORS = {
    'FIRE': 'orangered',
    'EARTH': 'saddlebrown',
    'AIR': 'deepskyblue',
    'WATER': 'mediumblue',
}

SIGN_ELEMENTS = {
    const.ARIES: 'FIRE', const.LEO: 'FIRE', const.SAGITTARIUS: 'FIRE',
    const.TAURUS: 'EARTH', const.VIRGO: 'EARTH', const.CAPRICORN: 'EARTH',
    const.GEMINI: 'AIR', const.LIBRA: 'AIR', const.AQUARIUS: 'AIR',
    const.CANCER: 'WATER', const.SCORPIO: 'WATER', const.PISCES: 'WATER',
}


@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
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

        # Створення карти
        objects = [const.SUN, const.MOON, const.MERCURY, const.VENUS,
                   const.MARS, const.JUPITER, const.SATURN, const.URANUS,
                   const.NEPTUNE, const.PLUTO]
        chart = Chart(dt, geo, objects=objects)

        # Малюємо графіку
        fig, ax = plt.subplots(figsize=(8,8))
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')

        # Коло натальної карти
        circle = Circle((0,0), 1, edgecolor='black', facecolor='white', lw=2)
        ax.add_patch(circle)

        # Домашні сектори (12 будинків)
        for i in range(12):
            start_angle = i * 30
            wedge = Wedge((0,0), 1, start_angle, start_angle+30,
                          facecolor='none', edgecolor='gray', lw=1, linestyle='--')
            ax.add_patch(wedge)
            # Номер будинку
            angle_rad = np.deg2rad(start_angle + 15)
            x = 1.05 * np.cos(angle_rad)
            y = 1.05 * np.sin(angle_rad)
            ax.text(x, y, str(i+1), ha='center', va='center', fontsize=8, color='gray')

        # Планети у колі з кольорами за стихіями
        for obj in chart.objects:
            element = SIGN_ELEMENTS.get(obj.sign.id, 'AIR')
            color = ELEMENT_COLORS.get(element, 'black')
            angle = np.deg2rad(obj.sign.lon)
            x = 0.8 * np.cos(angle)
            y = 0.8 * np.sin(angle)
            ax.plot(x, y, 'o', markersize=12, color=color)
            ax.text(x, y, obj.id, ha='center', va='center', fontsize=9, color='black')

        # Аспекти
        for i, obj1 in enumerate(chart.objects):
            for j, obj2 in enumerate(chart.objects):
                if j <= i:
                    continue
                asp = aspects.getAspect(obj1, obj2)
                if asp:
                    angle1 = np.deg2rad(obj1.sign.lon)
                    angle2 = np.deg2rad(obj2.sign.lon)
                    x1, y1 = 0.8 * np.cos(angle1), 0.8 * np.sin(angle1)
                    x2, y2 = 0.8 * np.cos(angle2), 0.8 * np.sin(angle2)
                    ax.plot([x1, x2], [y1, y2], color='gray', lw=1, alpha=0.5)

        # Логотип у центрі
        ax.text(0, 0, "Albireo Daria", ha='center', va='center', fontsize=12, color='darkred', fontweight='bold')

        chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
        plt.savefig(chart_path, dpi=150)
        plt.close(fig)

        return jsonify({'chart_image_url': f'/static/chart.png'}), 200

    except Exception as e:
        print("Помилка генерації карти:", e)
        return jsonify({'chart_image_url': '/static/chart.png'}), 200


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)