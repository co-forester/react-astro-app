from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import matplotlib.pyplot as plt
import math
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

PLANETS = [
    const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
    const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
]

ASPECTS = [
    (const.CONJUNCTION, 0),
    (const.SEXTILE, 60),
    (const.SQUARE, 90),
    (const.TRINE, 120),
    (const.OPPOSITION, 180)
]

ASPECT_COLORS = {
    const.CONJUNCTION: 'black',
    const.SEXTILE: 'green',
    const.SQUARE: 'red',
    const.TRINE: 'blue',
    const.OPPOSITION: 'magenta'
}

def geocode_location(location_name):
    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(location_name)
    if loc:
        tf = TimezoneFinder()
        tzname = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        tz = pytz.timezone(tzname)
        return loc.latitude, loc.longitude, tz
    else:
        raise ValueError("Location not found")

def get_aspects(chart):
    aspect_list = []
    for i, p1 in enumerate(PLANETS):
        obj1 = chart.get(p1)
        for j in range(i+1, len(PLANETS)):
            p2 = PLANETS[j]
            obj2 = chart.get(p2)
            for asp_type, asp_angle in ASPECTS:
                asp = aspects.getAspect(obj1, obj2, asp_angle)
                if asp:
                    aspect_list.append({
                        'planet1': p1,
                        'aspect': asp_type,
                        'planet2': p2,
                        'degree': round(asp.orb, 2)
                    })
    return aspect_list

def draw_chart(chart, filename='chart.png'):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection':'polar'})
    ax.set_ylim(0, 1)
    ax.set_theta_zero_location('E')
    ax.set_theta_direction(-1)
    ax.set_xticks([math.radians(x) for x in range(0, 360, 30)])
    ax.set_xticklabels([f'{i}°' for i in range(0, 360, 30)])
    ax.set_yticklabels([])

    # Draw house divisions
    for h in range(1, 13):
        cusp = chart.get(const.HOUSES[h-1]).lon
        ax.plot([math.radians(cusp), math.radians(cusp)], [0, 1], color='lightgray', linestyle='--')

    # Draw planets and ASC/MC
    positions = {}
    for p in PLANETS + [const.ASC, const.MC]:
        obj = chart.get(p)
        lon_rad = math.radians(obj.lon)
        positions[p] = lon_rad
        ax.plot(lon_rad, 0.85, 'o', markersize=12, color='gold', markeredgecolor='black')
        ax.text(lon_rad, 0.9, f"{p}\n{int(obj.lon)}°", ha='center', va='center', fontsize=9, fontweight='bold')

    # Draw aspects
    for asp in get_aspects(chart):
        lon1 = positions[asp['planet1']]
        lon2 = positions[asp['planet2']]
        color = ASPECT_COLORS[asp['aspect']]
        ax.plot([lon1, lon2], [0.85, 0.85], color=color, linewidth=1.5, alpha=0.7)

    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close()

def generate_aspects_table(aspect_list):
    html = "<table><tr><th>Планета 1</th><th>Аспект</th><th>Планета 2</th><th>Градус</th></tr>"
    for a in aspect_list:
        html += f"<tr><td>{a['planet1']}</td><td>{a['aspect']}</td><td>{a['planet2']}</td><td>{a['degree']}</td></tr>"
    html += "</table>"
    return html

@app.route('/generate', methods=['POST'])
def generate_chart_route():
    data = request.json
    try:
        dt_str = data['datetime']  # 'YYYY-MM-DD HH:MM'
        location = data['location']  # city name

        # Геокодування
        lat, lon, tz = geocode_location(location)

        # Парсинг дати і часу через стандартний datetime
        date_part, time_part = dt_str.split()
        dt_python = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        dt_obj = Datetime(dt_python.strftime("%Y-%m-%d"), dt_python.strftime("%H:%M"), tz.zone)

        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)  # Placidus
        aspects_list = get_aspects(chart)
        draw_chart(chart, 'chart.png')
        table_html = generate_aspects_table(aspects_list)

        return jsonify({
            'aspects_table_html': table_html,
            'chart_image_url': '/chart.png'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/chart.png')
def chart_png():
    if os.path.exists('chart.png'):
        return send_file('chart.png', mimetype='image/png')
    return "No chart generated yet", 404

@app.route('/health')
def health():
    return "Server is healthy", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    