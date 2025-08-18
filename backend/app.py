from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.get_json()
        date_str = data['date']
        time_str = data['time']
        place_str = data['place']

        # Геолокація
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place_str)
        if not location:
            return jsonify({'error': 'Place not found'}), 400

        latitude = location.latitude
        longitude = location.longitude

        # Часовий пояс
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=latitude, lng=longitude)
        tz = pytz.timezone(tz_name)

        # Обробка дати і часу
        dt_naive = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        dt_local = tz.localize(dt_naive)
        dt_utc = dt_local.astimezone(pytz.utc)

        # Flatlib datetime
        dt_flat = Datetime(dt_utc.strftime('%Y-%m-%d'), dt_utc.strftime('%H:%M'), '+0')

        # Створення натальної карти
        chart = Chart(dt_flat, GeoPos(latitude, longitude))

        # Побудова простого графіка (як приклад)
        fig, ax = plt.subplots(figsize=(6,6))
        ax.text(0.5, 0.5, 'Натальна карта', fontsize=18, ha='center')
        ax.axis('off')
        plt.savefig('chart.png')
        plt.close()

        return jsonify({'message': 'Chart generated', 'chart_url': '/chart.png'})

    except Exception as e:
        return jsonify({'error': str(e), 'trace': repr(e)}), 500

@app.route('/chart.png')
def get_chart():
    return send_file('chart.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(port=8080, debug=True)