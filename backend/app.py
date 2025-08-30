import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from matplotlib.text import TextPath
from matplotlib.transforms import Affine2D
from matplotlib.font_manager import FontProperties

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const

# ----------------- App -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Constants -----------------
PLANET_SYMBOLS = {
    const.SUN: '☉', const.MOON: '☽', const.MERCURY: '☿', const.VENUS: '♀',
    const.MARS: '♂', const.JUPITER: '♃', const.SATURN: '♄', const.URANUS: '♅',
    const.NEPTUNE: '♆', const.PLUTO: '♇', const.TRUE_NODE: '☊', const.CHIRON: '⚷'
}

ASPECT_COLORS = {
    const.CONJUNCTION: 'red',
    const.SEXTILE: 'green',
    const.SQUARE: 'orange',
    const.TRINE: 'blue',
    const.OPPOSITION: 'purple'
}

ZODIAC_SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]

# ----------------- Helper Functions -----------------
def draw_natal_chart(chart, filename="static/chart.png"):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.axis('off')

    # Основне коло зодіаку
    zodiac_radius_outer = 0.95
    zodiac_radius_inner = 0.75
    for i, sign in enumerate(ZODIAC_SIGNS):
        start = i * 30
        wedge = Wedge((0,0), zodiac_radius_outer, start, start+30, width=0.2, facecolor='#f0f0f0', edgecolor='black')
        ax.add_patch(wedge)
        # Надпис знака по дузі, ближче до центру
        angle_rad = math.radians(start + 15)
        ax.text(0.85*math.cos(angle_rad), 0.85*math.sin(angle_rad), sign, ha='center', va='center', rotation=start+15+90, rotation_mode='anchor', fontsize=10, fontweight='bold')

    # Сектори домів з точним розділенням
    for house in chart.houses:
        angle = (house.lon % 360)
        ax.plot([0.75*math.cos(math.radians(angle)), 0.95*math.cos(math.radians(angle))],
                [0.75*math.sin(math.radians(angle)), 0.95*math.sin(math.radians(angle))],
                color='black', linewidth=1)

    # AC, DC, IC, VC
    angles_points = {'AC': chart.houses[0].lon, 'DC': (chart.houses[0].lon+180)%360,
                     'IC': chart.houses[3].lon, 'VC': (chart.houses[3].lon+180)%360}
    for point, angle in angles_points.items():
        ax.text(1.05*math.cos(math.radians(angle)), 1.05*math.sin(math.radians(angle)), point, fontsize=12, fontweight='bold', color='darkred', ha='center', va='center')

    # Планети великими символами з градусами
    for p in chart.objects:
        if p.name in PLANET_SYMBOLS:
            angle = p.lon
            radius = 0.65
            symbol = PLANET_SYMBOLS[p.name]
            deg = int(p.lon)
            ax.text(radius*math.cos(math.radians(angle)), radius*math.sin(math.radians(angle)),
                    f'{symbol} {deg}°', fontsize=16, ha='center', va='center', fontweight='bold')

    # Аспекти
    for asp in chart.aspects:
        if asp.type in ASPECT_COLORS:
            p1 = chart.get(asp.p1)
            p2 = chart.get(asp.p2)
            angle1 = math.radians(p1.lon)
            angle2 = math.radians(p2.lon)
            ax.plot([0.65*math.cos(angle1),0.65*math.cos(angle2)],
                    [0.65*math.sin(angle1),0.65*math.sin(angle2)],
                    color=ASPECT_COLORS[asp.type], linewidth=1)

    # Лого в центр
    ax.text(0,0,'✨MyLogo✨', fontsize=14, ha='center', va='center', fontweight='bold', color='darkblue')

    fig.savefig(filename, dpi=150)
    plt.close(fig)

# ----------------- Routes -----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    date = data.get("date")  # YYYY-MM-DD
    time = data.get("time")  # HH:MM
    place = data.get("place")  # city, country

    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place)
    if not location:
        return jsonify({"error":"Place not found"}), 400

    tz = TimezoneFinder().timezone_at(lng=location.longitude, lat=location.latitude)
    local_dt = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    local_dt = pytz.timezone(tz).localize(local_dt)

    chart = Chart(local_dt, location.latitude, location.longitude)

    # Генеруємо картинку
    os.makedirs("static", exist_ok=True)
    draw_natal_chart(chart, filename="static/chart.png")

    # Повертаємо JSON
    response = {
        "chart_url": "/static/chart.png",
        "planets": {p.name: p.lon for p in chart.objects}
    }
    return jsonify(response)

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)