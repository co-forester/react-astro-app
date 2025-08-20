import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
CORS(app)

# Створюємо папку static якщо немає
if not os.path.exists('static'):
    os.makedirs('static')

# Шлях до логотипів-піктограм для планет (приклад)
PLANET_ICONS = {
    'Sun': 'static/icons/sun.png',
    'Moon': 'static/icons/moon.png',
    'Mercury': 'static/icons/mercury.png',
    'Venus': 'static/icons/venus.png',
    'Mars': 'static/icons/mars.png',
    'Jupiter': 'static/icons/jupiter.png',
    'Saturn': 'static/icons/saturn.png',
    'Uranus': 'static/icons/uranus.png',
    'Neptune': 'static/icons/neptune.png',
    'Pluto': 'static/icons/pluto.png'
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

        # Приклад координат, замініть на геокодинг
        lat, lon = 50.4501, 30.5234
        dt = Datetime(f"{date} {time}", '+03:00')
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo)

        # Малюємо коло натальної карти
        fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'polar': True})
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylim(0,1)

        # Основне коло
        circle = plt.Circle((0.5, 0.5), 0.45, transform=ax.transAxes,
                            fill=False, color='blue', linewidth=2)
        ax.add_artist(circle)

        # Логотип по колу всередині карти
        logo_text = "Abireo Daria"
        n = len(logo_text)
        radius = 0.48
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        for i, char in enumerate(logo_text):
            angle = angles[i]
            x = 0.5 + radius * np.cos(angle)
            y = 0.5 + radius * np.sin(angle)
            rotation = np.degrees(angle) + 90
            ax.text(x, y, char, rotation=rotation,
                    ha='center', va='center', fontsize=10, color='purple')

        # Додаємо піктограми планет по колу (для прикладу)
        planet_radius = 0.35
        planet_angles = np.linspace(0, 2*np.pi, len(chart.objects), endpoint=False)
        for i, obj in enumerate(chart.objects):
            planet_name = obj.id
            angle = planet_angles[i]
            x = 0.5 + planet_radius * np.cos(angle)
            y = 0.5 + planet_radius * np.sin(angle)
            icon_path = PLANET_ICONS.get(planet_name)
            if icon_path and os.path.exists(icon_path):
                img = plt.imread(icon_path)
                ax.imshow(img, extent=(x-0.03, x+0.03, y-0.03, y+0.03), zorder=10)

        ax.set_title(f"Натальна карта: {place}", fontsize=14)
        chart_path = os.path.join('static', 'chart.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close(fig)

        return jsonify({'chart_image_url': '/static/chart.png'})

    except Exception as e:
        print(e)
        return jsonify({'error': 'Помилка генерації карти'}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)