from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
CORS(app)

EPHE_PATH = '/data/ephe'
CHART_PATH = '/app/chart.png'

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Невірні дані'}), 400

    date = data.get('date')
    time = data.get('time')
    place = data.get('place')  # місто + країна
    timezone = data.get('timezone', 'Europe/Kiev')

    if not date or not time or not place:
        return jsonify({'error': 'Невірні дані'}), 400

    try:
        # Просте геокодування через GeoPos, можна замінити на Geopy для точного
        # Тут розбиваємо place на місто та країну, якщо потрібно
        lat, lon = 46.975, 31.994  # координати Миколаїв (приклад)
        pos = GeoPos(lat, lon)

        dt = Datetime(date, time, timezone)
        chart = Chart(dt, pos, IDs=const.LIST_OBJECTS)

        object_data = []
        for obj in chart.objects:
            # беремо швидкість через ecl_lon_speed
            object_data.append({
                'id': obj.id,
                'sign': obj.sign,
                'lon': round(obj.lon, 2),
                'lat': round(obj.lat, 2),
                'speed': round(obj.ecl_lon_speed, 2)
            })

        # Малюємо просту карту
        plt.figure(figsize=(6,6))
        plt.title(f'Natal Chart for {date} {time}')
        for obj in chart.objects:
            plt.plot(obj.lon, obj.lat, 'o', label=obj.id)
        plt.legend()
        plt.savefig(CHART_PATH)
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