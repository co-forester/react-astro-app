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

@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.get_json()

    first_name = data.get("firstName", "")
    last_name = data.get("lastName", "")

    # Використовуємо datetime + location або date + time + place
    datetime_str = data.get("datetime")
    location_str = data.get("location")
    if not datetime_str or not location_str:
        date = data.get("date")
        time = data.get("time")
        place = data.get("place")
        if date and time and place:
            datetime_str = f"{date} {time}"
            location_str = place

    if not datetime_str or not location_str:
        return jsonify({"error": "Missing 'datetime'/'date+time' or 'location'/'place' field"}), 400

    try:
        dt = Datetime(datetime_str, 'UTC')
    except Exception as e:
        return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400

    try:
        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(location_str)
        if not loc:
            return jsonify({"error": f"Could not find location '{location_str}'"}), 400
        geo = GeoPos(loc.latitude, loc.longitude)
    except Exception as e:
        return jsonify({"error": f"Geocoding error: {str(e)}"}), 400

    try:
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        timezone = pytz.timezone(tz_str) if tz_str else pytz.UTC
        dt_localized = dt.replace(tzinfo=pytz.UTC).astimezone(timezone)
    except Exception as e:
        return jsonify({"error": f"Timezone error: {str(e)}"}), 400

    try:
        chart = Chart(dt_localized, geo)
    except Exception as e:
        return jsonify({"error": f"Chart generation error: {str(e)}"}), 500

    # Створимо просту таблицю аспектів
    aspects_list = []
    for obj1 in chart.objects:
        for obj2 in chart.objects:
            if obj1 != obj2:
                for asp in aspects.ASPECTS:
                    if aspects.aspect(obj1, obj2, asp['angle'], orb=1):
                        aspects_list.append({
                            "object1": obj1.id,
                            "object2": obj2.id,
                            "aspect": asp['name'],
                            "angle": asp['angle']
                        })

    # Малюємо просту натальну карту
    fig, ax = plt.subplots(figsize=(6,6))
    ax.set_title(f"Natal Chart: {first_name} {last_name}".strip())
    ax.plot([0], [0], 'ro')
    plt.savefig("chart.png")
    plt.close()

    return jsonify({
        "firstName": first_name,
        "lastName": last_name,
        "datetime": datetime_str,
        "location": location_str,
        "aspects": aspects_list,
        "chartImage": "/chart.png"
    })

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