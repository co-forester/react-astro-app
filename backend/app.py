from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import matplotlib.pyplot as plt
import os
import pytz

app = Flask(__name__)
CORS(app)

CHART_PATH = '/app/chart.png'


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

        # Малюємо PNG
        plt.figure(figsize=(6, 6))
        plt.title(f'Natal Chart for {date} {time} ({place})')
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