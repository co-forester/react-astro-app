from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
import pytz
import os

app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.get_json()
        date = data.get('date')
        time = data.get('time')
        place_name = data.get('place')

        # Геокодування місця
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place_name)
        if location is None:
            return jsonify({'error': 'Місце не знайдено'}), 400
        geo = GeoPos(location.latitude, location.longitude)

        # Знаходження часового поясу
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        if tz_str is None:
            tz_str = 'UTC'
        timezone = pytz.timezone(tz_str)

        # Обробка дати та часу
        dt = Datetime(date, time, tz_str)
        chart = Chart(dt, geo)

        # Малюємо просту карту
        fig, ax = plt.subplots(figsize=(6,6))
        ax.text(0.5, 0.5, 'Astro Chart', fontsize=20, ha='center')
        plt.axis('off')
        chart_path = os.path.join(os.getcwd(), 'chart.png')
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()

        return jsonify({
            'message': 'Карта згенерована',
            'chart_url': '/chart.png'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'trace': repr(e)
        }), 500

@app.route('/chart.png')
def get_chart():
    chart_path = os.path.join(os.getcwd(), 'chart.png')
    if os.path.exists(chart_path):
        return send_file(chart_path, mimetype='image/png')
    else:
        return jsonify({'error': 'Файл карти не знайдено'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)