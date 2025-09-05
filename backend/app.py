import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# ---------- Константи ----------
PLANET_SYMBOLS = {
    const.SUN: "☉", const.MOON: "☽", const.MERCURY: "☿",
    const.VENUS: "♀", const.MARS: "♂", const.JUPITER: "♃",
    const.SATURN: "♄", const.URANUS: "♅", const.NEPTUNE: "♆",
    const.PLUTO: "♇", const.NORTH_NODE: "☊", const.SOUTH_NODE: "☋",
}

ASPECT_COLORS = {
    'conj': '#FF0000', 'opp': '#800080', 'trine': '#00FF00', 'sq': '#FFA500', 'sextile': '#0000FF'
}

HOUSES_COLORS = ['#FFE0B2', '#FFCC80', '#FFB74D', '#FFA726', '#FF9800', '#FB8C00',
                 '#F57C00', '#EF6C00', '#E65100', '#FFECB3', '#FFE082', '#FFD54F']

# ---------- Flask ----------
app = Flask(__name__)
CORS(app)

# ---------- Допоміжні функції ----------
def dms(degree):
    d = int(degree)
    m = int((degree - d) * 60)
    s = int((((degree - d) * 60) - m) * 60)
    return f"{d}°{m}'{s}\""

def get_planet_coords(chart):
    coords = {}
    for p in chart.objects:
        if p.TYPE in PLANET_SYMBOLS:
            try:
                lon = p.lon
            except:
                lon = 0.0
            coords[p.TYPE] = lon
    return coords

def get_house_cusps(chart):
    cusps = {}
    for i in range(1, 13):
        try:
            lon = chart.houses[i].lon
        except:
            lon = 0.0
        cusps[i] = lon
    return cusps

# ---------- Малювання карти ----------
def draw_chart(chart, filename='chart.png'):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1)  # проти годинникової
    ax.set_theta_offset(math.radians(math.pi/2))  # 0° вгорі
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Домів сектора
    cusps = get_house_cusps(chart)
    for i, lon in cusps.items():
        angle = math.radians(lon)
        ax.bar(angle, 1.0, width=math.radians(30), bottom=0.0, color=HOUSES_COLORS[i-1], edgecolor='k', alpha=0.3)
    
    # Зодіак
    for i in range(12):
        start = math.radians(i*30)
        ax.text(start + math.radians(15), 1.05, const.SIGN_SYMBOLS[i+1], fontsize=14,
                ha='center', va='center')
    
    # ASC/MC/IC/DSC
    for point in ['ASC','MC','IC','DSC']:
        try:
            obj = getattr(chart, point)
            deg = obj.lon % 30
            sign = const.SIGN_SYMBOLS[int(obj.sign)]
            ax.text(math.radians(obj.lon), 1.15, f"{point} {deg:.1f}° {sign}", color='yellow', ha='center', va='center')
        except:
            pass
    
    # Планети
    planets = get_planet_coords(chart)
    for p, lon in planets.items():
        angle = math.radians(lon)
        ax.text(angle, 0.8, PLANET_SYMBOLS[p], fontsize=16, ha='center', va='center')
    
    # Аспекти
    try:
        for a in chart.aspects:
            if a.orb < 0.5:  # fallback малий орб
                continue
            lon1 = chart.get(a.obj1).lon
            lon2 = chart.get(a.obj2).lon
            angle1 = math.radians(lon1)
            angle2 = math.radians(lon2)
            ax.plot([angle1, angle2], [0.0, 0.8], color=ASPECT_COLORS.get(a.type, '#000000'), lw=1)
    except:
        pass
    
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename

# ---------- Генерація карти ----------
def generate_chart_image(date, time, city, country, filename='chart.png'):
    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(f"{city}, {country}")
    tf = TimezoneFinder()
    tzname = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
    tz = pytz.timezone(tzname)
    dt_obj = tz.localize(dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
    chart = Chart(Datetime(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute, tzname),
                  GeoPos(loc.latitude, loc.longitude), hsys='P')
    return draw_chart(chart, filename)

# ---------- API ----------
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    name = data.get("name", "Unknown")
    date_str = data.get("date")
    time_str = data.get("time")
    place = data.get("place", "Unknown")
    lat = data.get("lat")
    lon = data.get("lon")

    dt_obj = Datetime(date_str, time_str)
    pos = GeoPos(lat, lon)
    chart = Chart(dt_obj, pos, hsys='P')

    key = hashlib.md5(f"{name}{date_str}{time_str}{place}".encode()).hexdigest()
    png_path = os.path.join(CACHE_DIR, f"{key}.png")
    planets_list, aspect_lines = draw_chart(chart, png_path)

    out = {
        "name": name,
        "date": date_str,
        "time": time_str,
        "place": place,
        "chart_url": f"{request.host_url.rstrip('/')}/cache/{key}.png",
        "planets": planets_list,
        "aspects": aspect_lines
    }

    json_path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return jsonify(out)

@app.route("/cache/<filename>")
def serve_cache(filename):
    return app.send_static_file(os.path.join(CACHE_DIR, filename))

if __name__ == "__main__":
    app.run(debug=True)
# ----------------- Статика кешу -----------------
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)