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
from geopy.geocoders import Nominatim

# ====================== Flask ======================
app = Flask(__name__)
CORS(app)

# Статична папка для карт
STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

# Геолокатор
geolocator = Nominatim(user_agent="albireo_app")

# ====================== Ендпоінт генерації карти ======================
@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.json
        date = data.get('date')
        time = data.get('time')
        place = data.get('place')

        if not (date and time and place):
            return jsonify({'error': 'Введіть дату, час та місце'}), 400

        # ====================== Геокодування через geopy ======================
        location = geolocator.geocode(f"{place}, Україна")
        if not location:
            return jsonify({'error': 'Не вдалося знайти координати міста'}), 400

        lat, lon = location.latitude, location.longitude

        # ====================== Створення натальної карти ======================
        dt = Datetime(f"{date} {time}", '+03:00')  # Можна динамічно підставляти часовий пояс
        geo = GeoPos(lat, lon)
        chart = Chart(dt, geo)

        # ====================== Малювання карти ======================
        fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'polar': True})
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylim(0,1)

        # Коло карти
        circle = plt.Circle((0.5, 0.5), 0.45, transform=ax.transAxes,
                            fill=False, color='blue', linewidth=2)
        ax.add_artist(circle)

        # Логотип по колу
        text = "Abireo Daria"
        n = len(text)
        radius = 0.48
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        for i, char in enumerate(text):
            angle = angles[i]
            x = 0.5 + radius * np.cos(angle)
            y = 0.5 + radius * np.sin(angle)
            rotation = np.degrees(angle) + 90
            ax.text(x, y, char, rotation=rotation,
                    ha='center', va='center', fontsize=10, color='purple')

        ax.set_title(f"Натальна карта: {place}", fontsize=14)

        # ====================== Збереження карти ======================
        chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close(fig)

        return jsonify({'chart_image_url': f'/static/chart.png'})

    except Exception as e:
        print(e)
        return jsonify({'error': 'Помилка генерації карти'}), 500

# ====================== Доступ до статичних файлів ======================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

# ====================== Health Check ======================
@app.route('/health')
def health():
    return 'OK', 200

# ====================== Запуск сервера ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)