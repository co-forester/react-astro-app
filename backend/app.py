import os
import json
import math
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects, planets

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

HOUSE_COLORS = [
    "#fbe4e4", "#fef6e4", "#eaf6e4", "#e4f6f5",
    "#e4f0f6", "#e4eaf6", "#f0e4f6", "#f6e4f0",
    "#f6e4e4", "#f6f0e4", "#e4f6e8", "#e4f6f0"
]

ASPECT_COLORS = {
    "CONJ": "#FF0000",
    "OPP": "#0000FF",
    "TRI": "#00AA00",
    "SQR": "#FFA500",
    "SEX": "#800080",
}

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    name = data.get("name", "Unknown")
    date_str = data.get("date")
    time_str = data.get("time")
    place = data.get("place")

    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place)
    if not location:
        return jsonify({"error": "Місце не знайдено"}), 400
    lat, lon = location.latitude, location.longitude

    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=lat, lng=lon)
    tz = pytz.timezone(tz_str)

    dt_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_obj = tz.localize(dt_obj)
    date = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz_str)
    location_pos = GeoPos(lat, lon)

    key = f"{name}_{date_str}_{time_str}_{place}".replace(" ", "_")
    json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
    chart_path = os.path.join(CACHE_DIR, f"{key}.png")

    if os.path.exists(chart_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(chart_path))
        if datetime.now() - mtime < timedelta(days=30):
            with open(json_cache_path, "r", encoding="utf-8") as f:
                out = json.load(f)
            return jsonify(out)

    chart = Chart(date, location_pos, hsys="PLACIDUS")

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
    ax.set_facecolor("white")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_xticks([])
    ax.set_yticks([])

    # Домашні сектори
    for i in range(12):
        start = math.radians(i * 30)
        end = math.radians((i + 1) * 30)
        ax.bar(
            x=(start + end)/2,
            height=1.0,
            width=end-start,
            bottom=0,
            color=HOUSE_COLORS[i % len(HOUSE_COLORS)],
            edgecolor="white"
        )
        ax.text(
            x=start + math.radians(15),
            y=0.55,
            s=f"{i+1}",
            ha="center",
            va="center",
            fontsize=12,
            weight="bold"
        )

    # Планети
    planets_list = [const.SUN, const.MOON, const.MERCURY, const.VENUS,
                    const.MARS, const.JUPITER, const.SATURN, const.URANUS,
                    const.NEPTUNE, const.PLUTO]
    planet_positions = {}
    for p in planets_list:
        obj = chart.get(p)
        angle = math.radians(obj.signlon % 360)
        planet_positions[p] = angle
        ax.plot(angle, 0.8, 'o', markersize=8, label=p)
        deg = int(obj.lon)
        min = int((obj.lon - deg) * 60)
        sec = int(((obj.lon - deg) * 60 - min) * 60)
        ax.text(angle, 0.85, f"{p}\n{deg}°{min}'{sec}\"", ha="center", va="center", fontsize=9)

    # Аспекти
    aspect_list = []
    for i, p1 in enumerate(planets_list):
        for j, p2 in enumerate(planets_list):
            if j <= i:
                continue
            a = aspects.getAspect(chart.get(p1), chart.get(p2))
            if a:
                angle1 = planet_positions[p1]
                angle2 = planet_positions[p2]
                ax.plot([angle1, angle2], [0.8, 0.8], color=ASPECT_COLORS.get(a.type, "#888888"))
                aspect_list.append({
                    "planet1": p1,
                    "planet2": p2,
                    "type": a.type,
                    "orb": round(a.orb, 2)
                })

    ax.text(0, 0, name, ha="center", va="center", fontsize=14, weight="bold")

    try:
        plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)

    out = {
        "name": name,
        "date": date_str,
        "time": time_str,
        "place": place,
        "timezone": tz_str,
        "aspects_json": aspect_list,
        "chart_url": f"/cache/{key}.png"
    }
    with open(json_cache_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return jsonify(out)

@app.route("/cache/<filename>")
def serve_cache(filename):
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)