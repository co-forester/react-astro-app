import os
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
from geopy.geocoders import Nominatim

app = Flask(__name__)
CORS(app)

# Геокодування міста
def get_coordinates(place_name):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place_name)
    if not location:
        raise ValueError("Place not found")
    return location.latitude, location.longitude

# Побудова натальної карти
def build_chart(date, time, place):
    lat, lon = get_coordinates(place)
    dt = Datetime(date, time, '+03:00')  # або визначати динамічно
    geo = GeoPos(lat, lon)
    chart = Chart(dt, geo, hsys='P')
    return chart

# Малювання карти професійно
def draw_chart(chart):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.1,1.1)
    ax.set_ylim(-1.1,1.1)
    ax.axis('off')

    # Коло зодіаку
    circle = plt.Circle((0,0), 0.9, color='#f0f0f0', fill=True, linewidth=2)
    ax.add_artist(circle)

    # Знаки зодіаку по колу
    signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    for i, sign in enumerate(signs):
        angle = 90 - i*30
        x = 0.8 * np.cos(np.radians(angle))
        y = 0.8 * np.sin(np.radians(angle))
        ax.text(x, y, sign, ha='center', va='center', fontsize=10, fontweight='bold')

    # Логотип по центру
    ax.text(0, 0, '⭐', ha='center', va='center', fontsize=25, fontweight='bold', color='#8B0000')

    # Планети на колі
    planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
    colors = ['gold','silver','gray','pink','red','orange','brown','blue','navy','purple']
    for i, planet in enumerate(planets):
        obj = chart.get(planet)
        lon = float(obj.lon)
        angle = 90 - lon
        x = 0.7 * np.cos(np.radians(angle))
        y = 0.7 * np.sin(np.radians(angle))
        ax.text(x, y, planet, ha='center', va='center', fontsize=9, color=colors[i], fontweight='bold')

    # Збереження
    plt.savefig('chart.png', bbox_inches='tight', dpi=150)
    plt.close(fig)

# Аспекти
def get_aspects(chart):
    aspect_list = []
    planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
    for i in range(len(planets)):
        for j in range(i+1, len(planets)):
            a = aspects.getAspect(chart.get(planets[i]), chart.get(planets[j]))
            if a:
                aspect_list.append({
                    'from': planets[i],
                    'to': planets[j],
                    'type': a.type,
                    'angle': a.angle
                })
    return aspect_list

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    try:
        chart = build_chart(data['date'], data['time'], data['place'])
        draw_chart(chart)

        response = {
            'firstName': data.get('firstName'),
            'lastName': data.get('lastName'),
            'planets': {p: chart.get(p).sign for p in [const.SUN,const.MOON,const.MERCURY,const.VENUS,const.MARS,const.JUPITER,const.SATURN,const.URANUS,const.NEPTUNE,const.PLUTO]},
            'ascendant': chart.get(const.ASC).sign,
            'midheaven': chart.get(const.MC).sign,
            'aspects': get_aspects(chart),
            'houses': {str(i+1): chart.getHouse(i+1).sign for i in range(12)},
            'chartImage': '/chart.png'
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/chart.png')
def get_chart_image():
    if os.path.exists('chart.png'):
        return send_file('chart.png', mimetype='image/png')
    return "Chart not found", 404

@app.route('/health')
def health():
    return "Server is healthy", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)