import os
import math
import json
from datetime import datetime, timedelta
from hashlib import md5

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Кольори аспектів
ASPECT_COLORS = {
    "conjunction": "#ccc",
    "sextile": "#f7eaea",
    "square": "#8b8b8b",
    "trine": "#d4a5a5",
    "opposition": "#4a0f1f"
}

# ====================== Кеш ======================
def cache_key(name, date, time, place):
    key_str = f"{name}|{date}|{time}|{place}"
    return md5(key_str.encode()).hexdigest()

def clean_cache(days=30):
    now = datetime.now()
    for fname in os.listdir(CACHE_DIR):
        path = os.path.join(CACHE_DIR, fname)
        if os.path.isfile(path):
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime > timedelta(days=days):
                os.remove(path)

# ====================== Малюємо карту ======================
def draw_natal_chart(chart, aspects_list, save_path="chart.png"):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.axis("off")

    # Коло натальної карти
    circle = plt.Circle((0, 0), 1, fill=False, color="#4a0f1f", lw=2)
    ax.add_artist(circle)

    # Зодіакальні знаки
    zodiac_signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sign in enumerate(zodiac_signs):
        angle = 2*math.pi/12 * i
        x = 1.1 * math.cos(angle)
        y = 1.1 * math.sin(angle)
        ax.text(x, y, sign, fontsize=14, ha="center", va="center", color="#4a0f1f")

    # Планети
    planet_symbols = {
        "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
        "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
        "North Node":"☊","South Node":"☋","Pars Fortuna":"⚳","Syzygy":"☌"
    }
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x = 0.75 * math.cos(angle)
        y = 0.75 * math.sin(angle)
        ax.plot(x, y, "o", color="#6a1b2c", markersize=10)
        ax.text(x, y, planet_symbols.get(obj.id, obj.id), fontsize=12, ha="center", va="center", color="#4a0f1f")

    # Аспекти
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.id == asp["planet1"])
        p2 = next(o for o in chart.objects if o.id == asp["planet2"])
        x1, y1 = 0.75*math.cos(math.radians(p1.lon)), 0.75*math.sin(math.radians(p1.lon))
        x2, y2 = 0.75*math.cos(math.radians(p2.lon)), 0.75*math.sin(math.radians(p2.lon))
        ax.plot([x1, x2], [y1, y2], color=asp["color"], lw=1)

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ====================== Аспекти ======================
def compute_aspects(chart):
    aspect_list = []
    aspect_types = {
        const.CONJUNCTION:"conjunction",
        const.SEXTILE:"sextile",
        const.SQUARE:"square",
        const.TRINE:"trine",
        const.OPPOSITION:"opposition"
    }
    for i, p1 in enumerate(chart.objects):
        for j, p2 in enumerate(chart.objects):
            if i >= j:
                continue
            asp = aspects.getAspect(p1, p2, orbs=None)
            if asp and asp.type in aspect_types:
                type_str = aspect_types[asp.type]
                aspect_list.append({
                    "planet1": p1.id,
                    "planet2": p2.id,
                    "type": type_str,
                    "color": ASPECT_COLORS.get(type_str, "#ccc"),
                    "angle": round(asp.angle,2),
                    "planet1_symbol": p1.id,
                    "planet2_symbol": p2.id
                })
    return aspect_list

# ====================== Генерація карти ======================
@app.route("/generate", methods=["POST"])
def generate():
    clean_cache()
    data = request.json
    name = data.get("name","")
    date_str = data.get("date","")
    time_str = data.get("time","")
    place = data.get("place","")

    key = cache_key(name,date_str,time_str,place)
    chart_path = os.path.join(CACHE_DIR, f"{key}.png")
    cache_path = os.path.join(CACHE_DIR, f"{key}.json")

    # Якщо є кеш
    if os.path.exists(cache_path) and os.path.exists(chart_path):
        with open(cache_path,"r") as f:
            return jsonify(json.load(f))

    # Геолокація
    loc = geolocator.geocode(place)
    if not loc:
        return jsonify({"error":"Місто не знайдено"}),400
    geo = GeoPos(loc.latitude, loc.longitude)

    # Часовий пояс
    tz_str = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {time_str}","%Y-%m-%d %H:%M"))

    # Flatlib Datetime
    offset_hours = local_dt.utcoffset().total_seconds()/3600
    fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)

    # Chart
    chart = Chart(fdate, geo)

    # Аспекти
    aspect_list = compute_aspects(chart)

    # Малюємо карту
    draw_natal_chart(chart, aspect_list, save_path=chart_path)

    # Кеш
    cache_data = {
        "name": name,
        "date": date_str,
        "time": time_str,
        "place": place,
        "timezone": tz_str,
        "aspects_json": aspect_list,
        "chart_url": f"/cache/{key}.png"
    }
    with open(cache_path,"w") as f:
        json.dump(cache_data,f)

    return jsonify(cache_data)

# ====================== Кеш-файли ======================
@app.route("/cache/<filename>")
def get_cache(filename):
    return send_from_directory(CACHE_DIR, filename)

# ====================== Health ======================
@app.route("/health")
def health():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)