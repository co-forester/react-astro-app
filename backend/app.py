import os
import math
import json
from datetime import datetime as dt
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
from flatlib import const

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ====================== Очистка старого кешу ======================
import time

def cleanup_cache(days=30):
    now = time.time()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.isfile(fpath):
            if now - os.path.getmtime(fpath) > days*24*3600:
                os.remove(fpath)

cleanup_cache()

# ====================== Кольори та символи ======================
ASPECT_COLORS = {
    "trine": "#d4a5a5",
    "square": "#8b8b8b",
    "opposition": "#4a0f1f",
    "sextile": "#f7eaea",
    "conjunction": "#ccc"
}

PLANET_SYMBOLS = {
    const.SUN: "☉",
    const.MOON: "☽",
    const.MERCURY: "☿",
    const.VENUS: "♀",
    const.MARS: "♂",
    const.JUPITER: "♃",
    const.SATURN: "♄",
    const.URANUS: "♅",
    const.NEPTUNE: "♆",
    const.PLUTO: "♇",
    const.NORTH_NODE: "☊",
    const.SOUTH_NODE: "☋",
    const.ASC: "Asc",
    const.MC: "MC"
}

PLANET_COLORS = {
    const.SUN: "gold",
    const.MOON: "silver",
    const.MERCURY: "darkorange",
    const.VENUS: "deeppink",
    const.MARS: "red",
    const.JUPITER: "royalblue",
    const.SATURN: "brown",
    const.URANUS: "deepskyblue",
    const.NEPTUNE: "mediumslateblue",
    const.PLUTO: "purple",
    const.ASC: "green",
    const.MC: "black"
}

# ====================== Ключ кешу ======================
def cache_key(name, date, time, place):
    key_str = f"{name}|{date}|{time}|{place}"
    return md5(key_str.encode()).hexdigest()

# ====================== Малювання натальної карти ======================
def draw_natal_chart(chart, aspects_list, name="Person", save_path="static/chart.png"):
    fig, ax = plt.subplots(figsize=(12, 12))  # більший діаметр
    ax.axis("off")

    # Коло карти
    circle = plt.Circle((0, 0), 1, fill=False, color="#4a0f1f", lw=2)
    ax.add_artist(circle)

    # Градуйована шкала градусів
    for deg in range(0, 360, 10):
        rad = math.radians(deg)
        x_outer = math.cos(rad)
        y_outer = math.sin(rad)
        x_inner = 0.95 * math.cos(rad)
        y_inner = 0.95 * math.sin(rad)
        ax.plot([x_inner, x_outer], [y_inner, y_outer], color="#888", lw=0.5)
        ax.text(1.05*x_outer, 1.05*y_outer, f"{deg}°", fontsize=7, ha="center", va="center", color="white")

    # Зодіакальні знаки
    zodiac_signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sign in enumerate(zodiac_signs):
        angle = math.radians(i*30 + 15)  # центр знаку у секторі
        x = 1.15 * math.cos(angle)
        y = 1.15 * math.sin(angle)
        ax.text(x, y, sign, fontsize=18, ha="center", va="center", color="white", fontweight="bold")

    # Сектори будинків (Placidus) - пастельні кольори
    house_colors = ["#ffd9d9", "#d9ffd9", "#d9d9ff", "#fff5d9", "#ffd9ff", "#d9ffff", "#ffe5d9", "#e5ffd9", "#e5d9ff", "#fff0d9", "#f0d9ff", "#d9fff0"]
    for i in range(12):
        theta1 = math.radians(i*30)
        theta2 = math.radians((i+1)*30)
        wedge = plt.patches.Wedge((0,0), 1, i*30, (i+1)*30, facecolor=house_colors[i], alpha=0.3)
        ax.add_artist(wedge)

    # Планети
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x = 0.75 * math.cos(angle)
        y = 0.75 * math.sin(angle)
        label = PLANET_SYMBOLS.get(obj.id, obj.id)
        color = PLANET_COLORS.get(obj.id, "#6a1b2c")
        ax.plot(x, y, "o", color=color, markersize=14)
        ax.text(x, y, label, fontsize=14, ha="center", va="center", color=color, fontweight="bold")

    # Аспекти
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.id==asp["planet1"])
        p2 = next(o for o in chart.objects if o.id==asp["planet2"])
        x1, y1 = 0.75*math.cos(math.radians(p1.lon)), 0.75*math.sin(math.radians(p1.lon))
        x2, y2 = 0.75*math.cos(math.radians(p2.lon)), 0.75*math.sin(math.radians(p2.lon))
        ax.plot([x1, x2],[y1,y2], color=asp["color"], lw=1.5, alpha=0.8)

    # Логотип Albireo Daria у секторі Скорпіона
    scorpio_idx = 7  # Скорпіон 8-й знак, індекс 7
    angle_mid = math.radians(scorpio_idx*30 + 15)
    x_logo = 1.2 * math.cos(angle_mid)
    y_logo = 1.2 * math.sin(angle_mid)
    ax.text(x_logo, y_logo, "Albireo Daria ♏", fontsize=14, ha="center", va="center", color="white", fontweight="bold")

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ====================== Аспекти ======================
def compute_aspects(chart):
    aspect_list = []
    aspects_def = [
        ("conjunction", 0, 8),
        ("sextile", 60, 6),
        ("square", 90, 6),
        ("trine", 120, 8),
        ("opposition", 180, 8)
    ]

    objects = chart.objects
    for i, p1 in enumerate(objects):
        for j, p2 in enumerate(objects):
            if i >= j:
                continue
            diff = abs(p1.lon - p2.lon)
            diff = diff if diff <= 180 else 360 - diff
            for name, angle, orb in aspects_def:
                if abs(diff - angle) <= orb:
                    aspect_list.append({
                        "planet1": p1.id,
                        "planet1_symbol": PLANET_SYMBOLS.get(p1.id, p1.id),
                        "planet2": p2.id,
                        "planet2_symbol": PLANET_SYMBOLS.get(p2.id, p2.id),
                        "type": name,
                        "color": ASPECT_COLORS.get(name, "#ccc"),
                        "angle": round(diff,2)
                    })
                    break
    return aspect_list

# ====================== Генерація карти ======================
@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        name = data.get("name", "Person")
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")

        # Кеш
        key = cache_key(name, date_str, time_str, place)
        cache_path = os.path.join(CACHE_DIR, f"{key}.json")
        chart_path = os.path.join(CACHE_DIR, f"{key}.png")

        if os.path.exists(cache_path) and os.path.exists(chart_path):
            with open(cache_path) as f:
                cached_data = json.load(f)
            return jsonify({**cached_data, "chart_url": f"/cache/{key}.png"})

        # Геолокація
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400
        lat, lon = location.latitude, location.longitude

        # Таймзона
        tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        tz = pytz.timezone(tz_str)

        # Локальний час
        naive_dt = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive_dt)
        offset_hours = local_dt.utcoffset().total_seconds()/3600

        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        chart = Chart(fdate, pos, houses="Placidus")

        # Аспекти
        aspect_list = compute_aspects(chart)

        # Малюємо карту
        os.makedirs(CACHE_DIR, exist_ok=True)
        draw_natal_chart(chart, aspect_list, name=name, save_path=chart_path)

        cache_data = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "aspects_json": aspect_list
        }
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)

        return jsonify({**cache_data, "chart_url": f"/cache/{key}.png"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================== Кеш файли ======================
@app.route("/cache/<filename>")
def get_cached_chart(filename):
    return send_from_directory(CACHE_DIR, filename)

# ====================== Health ======================
@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)