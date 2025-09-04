import os
import math
import json
import hashlib
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
    "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "North Node": "☊", "South Node": "☋", "Pars Fortuna": "⚶"
}

ASPECT_COLORS = {
    "conjunction": "#FF0000",
    "opposition": "#0000FF",
    "trine": "#00FF00",
    "square": "#FFA500",
    "sextile": "#1F77B4"
}

def draw_chart(chart, filename):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.2,1.2)
    ax.set_ylim(-1.2,1.2)
    ax.axis('off')

    # Зодіак (полярність)
    for i in range(12):
        start = 2*math.pi*(i/12)
        end = 2*math.pi*((i+1)/12)
        ax.plot([0, math.cos(start)], [0, math.sin(start)], color="grey", lw=1)

    # Планети
    planets_list = []
    for p in chart.objects:
        if p.isPlanet():
            angle = math.radians(p.lon)
            x, y = math.cos(angle), math.sin(angle)
            ax.text(x*1.05, y*1.05, PLANET_SYMBOLS.get(p.id, p.id), fontsize=12, ha='center', va='center')
            planets_list.append({
                "name": p.id,
                "symbol": PLANET_SYMBOLS.get(p.id, p.id),
                "lon": p.lon
            })

    # Аспекти прямими хордами
    aspect_lines = []
    for asp in aspects.find(chart):
        if asp.type in ASPECT_COLORS:
            p1 = next(o for o in chart.objects if o.id==asp.obj1)
            p2 = next(o for o in chart.objects if o.id==asp.obj2)
            x1, y1 = math.cos(math.radians(p1.lon)), math.sin(math.radians(p1.lon))
            x2, y2 = math.cos(math.radians(p2.lon)), math.sin(math.radians(p2.lon))
            ax.plot([x1, x2], [y1, y2], color=ASPECT_COLORS[asp.type], lw=1)
            aspect_lines.append({
                "planet1": p1.id,
                "planet1_symbol": PLANET_SYMBOLS.get(p1.id, p1.id),
                "planet2": p2.id,
                "planet2_symbol": PLANET_SYMBOLS.get(p2.id, p2.id),
                "type": asp.type,
                "angle_dms": f"{int(asp.angle)}°"
            })

    fig.savefig(filename, bbox_inches='tight')
    plt.close(fig)
    return planets_list, aspect_lines

@app.route("/generate", methods=["POST"])
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