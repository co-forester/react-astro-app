import os
import json
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.cbook import get_sample_data

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

HOUSE_COLORS = [
    "#fce4ec", "#e3f2fd", "#f3e5f5", "#e8f5e9",
    "#fff3e0", "#f9fbe7", "#ede7f6", "#fbe9e7",
    "#e0f7fa", "#f1f8e9", "#fffde7", "#fce4d6"
]

def geocode_place(place_name):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place_name)
    if location:
        return location.latitude, location.longitude
    return None, None

def draw_chart(chart, save_path, logo_path=None):
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
    ax.set_theta_offset(3.14159/2)
    ax.set_theta_direction(-1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#ffffff")

    # Домы
    for i in range(12):
        start = i*30
        wedge = Wedge(center=(0,0), r=1.0, theta1=start, theta2=start+30,
                      facecolor=HOUSE_COLORS[i], alpha=0.5)
        ax.add_patch(wedge)

    # Центр кола з лого
    if logo_path and os.path.exists(logo_path):
        with get_sample_data(logo_path) as file:
            img = plt.imread(file)
            im = OffsetImage(img, zoom=0.2)
            ab = AnnotationBbox(im, (0,0), frameon=False)
            ax.add_artist(ab)
    else:
        circle = Circle((0,0), 0.1, color="gold", zorder=5)
        ax.add_patch(circle)

    # Планети
    for obj in chart.objects:
        deg = obj.signlon % 30
        rad = (obj.signlon/180.0)*3.14159
        ax.plot(rad, 0.7, 'o', label=obj.id)

    # Легенда планет
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))

    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    name = data.get("name", "Anonymous")
    date_str = data.get("date")
    time_str = data.get("time")
    place = data.get("place")

    key = f"{name}_{date_str}_{time_str}_{place}".replace(" ", "_")
    json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
    chart_path = os.path.join(CACHE_DIR, f"{key}.png")

    if os.path.exists(json_cache_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(json_cache_path))
        if datetime.now() - mtime < timedelta(days=30):
            with open(json_cache_path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))

    lat, lon = geocode_place(place)
    if lat is None:
        return jsonify({"error": "Місце не знайдено"}), 400

    tz_str = TimezoneFinder().timezone_at(lat=lat, lng=lon) or "UTC"
    tz = pytz.timezone(tz_str)
    dt_obj = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))

    date = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz_str)
    location = GeoPos(lat, lon)
    chart = Chart(date, location, hsys="PLACIDUS")

    draw_chart(chart, chart_path, logo_path="logo.png")

    aspect_list = []
    for asp in chart.aspects:
        aspect_list.append({
            "type": asp.type,
            "from": asp.obj1.id,
            "to": asp.obj2.id,
            "orb": asp.orb
        })

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