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
from datetime import datetime

app = Flask(__name__)
CORS(app)

STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

geolocator = Nominatim(user_agent="albireo_app")
tf = TimezoneFinder()

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

    # Автоматичне визначення часового поясу
    tz_str = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
    tz = pytz.timezone(tz_str)

    # Локалізація дати і часу
    dt_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    dt_local = tz.localize(dt_naive)
    dt = Datetime(dt_local.strftime("%Y-%m-%d"),
                  dt_local.strftime("%H:%M"),
                  dt_local.strftime("%z"))

    geo = GeoPos(lat, lon)

    # Класична натальна карта
    objects = [const.SUN, const.MOON, const.MERCURY, const.VENUS,
               const.MARS, const.JUPITER, const.SATURN, const.URANUS,
               const.NEPTUNE, const.PLUTO]
    chart = Chart(dt, geo, objects=objects)

    # Малюємо просту картинку
    fig, ax = plt.subplots(figsize=(6,6))
    ax.text(0.5, 0.5, f'Натальна карта: {place}\nЧасовий пояс: {tz_str}',
            ha='center', va='center', fontsize=14)
    chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
    plt.savefig(chart_path)
    plt.close(fig)

    return jsonify({'chart_image_url': f'/static/chart.png'}), 200

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)