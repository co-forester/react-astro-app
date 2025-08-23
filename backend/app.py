from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib import chart as fl_chart, const, datetime as fl_datetime, aspects as fl_aspects
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

app = Flask(__name__)
CORS(app)

def get_coordinates(place_name):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place_name)
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError("Місто не знайдено")

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=lat, lng=lon)
    if tz_str:
        return tz_str
    else:
        raise ValueError("Не вдалося визначити часовий пояс")

def draw_chart(chart, chart_path):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')

    # Градієнтне заповнення секторів будинків
    for i in range(12):
        angle_start = i * 30
        angle_end = angle_start + 30
        theta = np.linspace(np.radians(angle_start), np.radians(angle_end), 50)
        x = np.concatenate(([0], np.cos(theta)))
        y = np.concatenate(([0], np.sin(theta)))
        ax.fill(x, y, color=plt.cm.viridis(i/12), alpha=0.2)

    # Коло зодіаку
    circle = plt.Circle((0, 0), 1, fill=False, linewidth=2, color='black')
    ax.add_artist(circle)

    # Лінії будинків
    for i in range(12):
        angle = i * 30
        x = [0, 1.1 * np.cos(np.radians(angle))]
        y = [0, 1.1 * np.sin(np.radians(angle))]
        ax.plot(x, y, color='grey', linewidth=1)

    # Знаки зодіаку
    zodiac_symbols = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
    for i, symbol in enumerate(zodiac_symbols):
        angle = i * 30 + 15
        ax.text(0.85 * np.cos(np.radians(angle)), 
                0.85 * np.sin(np.radians(angle)),
                symbol, ha='center', va='center', fontsize=14, color='darkblue')

    # Планети
    planet_colors = {
        const.SUN: 'gold',
        const.MOON: 'silver',
        const.MERCURY: 'darkgreen',
        const.VENUS: 'pink',
        const.MARS: 'red',
        const.JUPITER: 'orange',
        const.SATURN: 'brown',
        const.URANUS: 'cyan',
        const.NEPTUNE: 'blue',
        const.PLUTO: 'purple'
    }
    planet_positions = {}
    for obj in chart.objects:
        lon = obj.lon
        x = 0.7 * np.cos(np.radians(lon))
        y = 0.7 * np.sin(np.radians(lon))
        planet_positions[obj.id] = (x, y)
        ax.plot(x, y, 'o', color=planet_colors.get(obj.id, 'black'), markersize=10)
        ax.text(x*1.1, y*1.1, obj.id, ha='center', va='center', fontsize=10)

    # Аспекти
    aspect_colors = {
        'CONJ': 'black',
        'OPP': 'red',
        'TRI': 'green',
        'SQR': 'purple',
        'SEX': 'blue'
    }
    all_aspects = fl_aspects.getAspects(chart.objects)
    for asp in all_aspects:
        p1, p2 = asp.obj1.id, asp.obj2.id
        if p1 in planet_positions and p2 in planet_positions:
            x1, y1 = planet_positions[p1]
            x2, y2 = planet_positions[p2]
            ax.plot([x1, x2], [y1, y2], color=aspect_colors.get(asp.type, 'gray'), linewidth=1, alpha=0.7)

    # Логотип у центрі
    ax.text(0, 0, "Albireo Daria", ha='center', va='center', fontsize=12, fontweight='bold', color='purple')

    plt.savefig(chart_path, bbox_inches='tight', dpi=150)
    plt.close(fig)

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json
    date_str = data.get("date")
    time_str = data.get("time")
    place_name = data.get("place")

    if not date_str or not time_str or not place_name:
        return jsonify({"error": "date, time та place обов'язкові"}), 400

    try:
        lat, lon = get_coordinates(place_name)
        tz_str = get_timezone(lat, lon)
        dt = fl_datetime.Datetime(f"{date_str} {time_str}", tz_str)
        chart_obj = fl_chart.Chart(dt, f"{lat},{lon}", IDs=[const.SUN, const.MOON, const.MERCURY, const.VENUS,
                                                             const.MARS, const.JUPITER, const.SATURN,
                                                             const.URANUS, const.NEPTUNE, const.PLUTO])
        chart_path = "chart.png"
        draw_chart(chart_obj, chart_path)
        return jsonify({"chart_image_url": f"/static/{chart_path}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_file(filename)

if __name__ == '__main__':
    app.run(debug=True)