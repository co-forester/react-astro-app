import os
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
import matplotlib.pyplot as plt

# --- Нове ---
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz, datetime

app = Flask(__name__)
CORS(app)

# --- Кольори для планет і аспектів ---
PLANET_COLORS = {
    const.SUN: 'gold',
    const.MOON: 'silver',
    const.MERCURY: 'green',
    const.VENUS: 'pink',
    const.MARS: 'red',
    const.JUPITER: 'blue',
    const.SATURN: 'brown',
    const.URANUS: 'cyan',
    const.NEPTUNE: 'navy',
    const.PLUTO: 'purple'
}

ASPECT_COLORS = {
    'CONJ': 'red',
    'OPP': 'blue',
    'TRI': 'green',
    'SQR': 'orange',
    'SEX': 'purple'
}

HOUSES_COLORS = [
    '#ffe0b2', '#ffcc80', '#ffb74d', '#ffa726',
    '#ff9800', '#fb8c00', '#f57c00', '#ef6c00',
    '#e65100', '#ffccbc', '#ffab91', '#ff8a65'
]

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# --- Сумісність аспектів ---
def _get_aspects(chart):
    try:
        return aspects.getAspects(chart)
    except AttributeError:
        try:
            return aspects.getAspectsList(chart, aspects.MAJOR_ASPECTS)
        except Exception:
            return []

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.json
        date_in = data['date']   # YYYY-MM-DD
        time_in = data['time']   # HH:MM
        place = data['place']

        # --- Геокодування ---
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if location:
            lat, lon = location.latitude, location.longitude
        else:
            lat, lon = 50.45, 30.52  # fallback Київ

        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
        if not timezone_str:
            timezone_str = "Europe/Kiev"
        tz = pytz.timezone(timezone_str)

        dt_native = datetime.datetime.strptime(f"{date_in} {time_in}", "%Y-%m-%d %H:%M")
        offset = tz.utcoffset(dt_native)
        tz_offset_hours = int(offset.total_seconds() / 3600)
        tz_str = f"{tz_offset_hours:+03d}:00"

        date_str = dt_native.strftime("%Y/%m/%d")
        time_str = dt_native.strftime("%H:%M")
        dt = Datetime(date_str, time_str, tz_str)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)

        # --- Фігура ---
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis('off')

        # --- Кола будинків ---
        for i in range(12):
            ax.add_patch(plt.Circle((0, 0), 1 - i*0.08, fill=True, color=HOUSES_COLORS[i], alpha=0.3))

        # --- Коло знаків зодіаку ---
        for i, sign in enumerate(ZODIAC_SIGNS):
            angle = i * 30 + 15  # центр знаку
            x = 1.05 * np.cos(np.radians(angle))
            y = 1.05 * np.sin(np.radians(angle))
            ax.text(x, y, sign, ha='center', va='center', fontsize=10, fontweight='bold', color='darkblue')

        # --- Логотип Albireo Daria ---
        ax.text(0, 1.15, 'Albireo Daria', ha='center', va='center', fontsize=14, fontweight='bold', color='purple')

        # --- Планети ---
        for obj in chart.objects:
            x = 0.7 * np.cos(np.radians(obj.lon))
            y = 0.7 * np.sin(np.radians(obj.lon))
            ax.text(x, y, f"{obj.id}\n{obj.lon:.1f}°", color=PLANET_COLORS.get(obj.id, 'black'), fontsize=12, fontweight='bold', ha='center', va='center')

        # --- Аспекти з дугами ---
        for asp in _get_aspects(chart):
            p1 = chart.get(asp.p1)
            p2 = chart.get(asp.p2)
            # дуга по колу
            theta1 = np.radians(p1.lon)
            theta2 = np.radians(p2.lon)
            arc = np.linspace(theta1, theta2, 100)
            r = 0.65
            x_arc = r * np.cos(arc)
            y_arc = r * np.sin(arc)
            ax.plot(x_arc, y_arc, color=ASPECT_COLORS.get(asp.type, 'grey'), linewidth=1.5)

        chart_path = "chart.png"
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close(fig)

        # --- Таблиця аспектів ---
        aspects_table = "<table><tr><th>Планета 1</th><th>Аспект</th><th>Планета 2</th><th>Градус</th></tr>"
        for asp in _get_aspects(chart):
            aspects_table += f"<tr style='color:{ASPECT_COLORS.get(asp.type,'black')}'><td>{asp.p1}</td><td>{asp.type}</td><td>{asp.p2}</td><td>{asp.orb:.1f}</td></tr>"
        aspects_table += "</table>"

        return jsonify({
            "chart_image_url": f"/chart.png",
            "aspects_table_html": aspects_table
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chart.png')
def chart_image():
    return send_file("chart.png", mimetype='image/png')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)