import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import matplotlib.pyplot as plt
from PIL import Image

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return "Server is healthy", 200

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    date = data.get('date')  # YYYY-MM-DD
    time = data.get('time')  # HH:MM
    place = data.get('place')  # City, Country

    # Геокодування
    geolocator = Nominatim(user_agent="natal_chart_app")
    location = geolocator.geocode(place)
    if not location:
        return jsonify({'error': 'Place not found'}), 400

    lat, lon = location.latitude, location.longitude

    # Часовий пояс
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=lon, lat=lat)
    if not tz_str:
        return jsonify({'error': 'Timezone not found'}), 400

    # Створюємо Datetime для Flatlib
    try:
        dt = Datetime(date.replace('-', '/'), time, float(pytz.timezone(tz_str).utcoffset(None).total_seconds() / 3600))
    except Exception as e:
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400

    geo = GeoPos(lat, lon)

    # Створюємо карту
    try:
        chart = Chart(dt, geo, hsys='Placidus')  # Placidus
    except Exception as e:
        return jsonify({'error': f'Error creating chart: {str(e)}'}), 500

    # Планети та важливі точки
    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    points = {}
    for p in planets:
        try:
            obj = chart.get(p)
            points[p] = {
                'sign': obj.sign,
                'lon': obj.lon
            }
        except Exception as e:
            points[p] = {'error': str(e)}

    # Асцендент і Середина Неба
    try:
        points['Asc'] = chart.get('Asc').sign
        points['MC'] = chart.get('MC').sign
    except Exception as e:
        points['Asc'] = points['MC'] = {'error': str(e)}

    # Аспекти
    asp_list = []
    try:
        for a in aspects.getAspectList(chart, planets):
            asp_list.append({
                'type': a.type,
                'obj1': a.obj1.id,
                'obj2': a.obj2.id,
                'exact': a.isExact()
            })
    except Exception as e:
        asp_list.append({'error': str(e)})

    # Малюємо карту
    try:
        fig, ax = plt.subplots(figsize=(8,8))
        ax.axis('off')

        # Коло знаків зодіаку
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        for i, sign in enumerate(signs):
            angle = i * (360/12)
            ax.text(angle, 1.05, sign, ha='center', va='center', rotation=angle, transform=ax.transAxes)

        # TODO: додати логотип та інші елементи по колу
        plt.savefig('chart.png', bbox_inches='tight')
        plt.close(fig)
    except Exception as e:
        return jsonify({'error': f'Error drawing chart: {str(e)}'}), 500

    return jsonify({
        'firstName': first_name,
        'lastName': last_name,
        'planets': points,
        'aspects': asp_list,
        'chartUrl': '/chart.png'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
    