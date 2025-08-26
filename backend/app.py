import os
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
import numpy as np

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    date = data.get('date')      # формат "YYYY-MM-DD"
    time = data.get('time')      # формат "HH:MM"
    place_str = data.get('place')  # "City, Country"

    # Геокодування місця
    location = geolocator.geocode(place_str)
    if not location:
        return jsonify({"error": "Invalid place"}), 400

    lat, lon = location.latitude, location.longitude
    tz_str = tf.timezone_at(lng=lon, lat=lat)
    if not tz_str:
        tz_str = 'UTC'

    dt = Datetime(date.replace('-', '/'), time, pytz.timezone(tz_str).utcoffset(None).total_seconds() / 3600)
    geo = GeoPos(lat, lon)

    # Chart з системою будинків Placidus
    chart = Chart(dt, geo, hsys='P')

    # Планети
    planets = {}
    for body in const.BODIES:
        obj = chart.get(body)
        planets[body] = {
            'sign': obj.sign,
            'degree': obj.signlon
        }

    # Асцендент та МС
    asc = chart.get(const.ASC)
    mc = chart.get(const.MC)

    # Система будинків
    houses = {}
    for i in range(1, 13):
        h = chart.get(const.HOUSES[i-1])
        houses[f'house{i}'] = {
            'cusp': h.lon,
            'sign': h.sign
        }

    # Аспекти
    chart_aspects = []
    for asp in aspects.ALL:
        try:
            a = chart.aspect(asp)
            chart_aspects.append({
                'type': asp,
                'body1': a.obj1.id,
                'body2': a.obj2.id,
                'exact': a.isExact
            })
        except:
            continue

    # Побудова професійної карти з matplotlib
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.set_aspect('equal')
    ax.axis('off')

    # Коло зодіаку
    for i, sign in enumerate(const.SIGNS):
        angle = i * 30
        x = 0.8 * np.cos(np.radians(angle))
        y = 0.8 * np.sin(np.radians(angle))
        ax.text(x, y, sign, ha='center', va='center', fontsize=12)

    # Тут можна вставити логотип
    logo_img_path = 'logo.png'
    if os.path.exists(logo_img_path):
        logo_img = plt.imread(logo_img_path)
        ax.imshow(logo_img, extent=[-0.1,0.1,-0.1,0.1], zorder=10)

    chart_img_path = 'chart.png'
    plt.savefig(chart_img_path, dpi=150, bbox_inches='tight')
    plt.close()

    return jsonify({
        'firstName': first_name,
        'lastName': last_name,
        'planets': planets,
        'asc': {'sign': asc.sign, 'degree': asc.signlon},
        'mc': {'sign': mc.sign, 'degree': mc.signlon},
        'houses': houses,
        'aspects': chart_aspects,
        'chartImage': chart_img_path
    })

@app.route('/health')
def health():
    return "Server is healthy", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)