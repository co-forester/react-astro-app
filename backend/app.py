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
                        "angle": round(diff, 2)
                    })
                    break
    return aspect_list

# ====================== Малюємо натальну карту ======================
def draw_natal_chart(chart, aspects_list, name="Person", save_path="static/chart.png"):
    fig, ax = plt.subplots(figsize=(12, 12))  # Збільшено розмір
    ax.axis("off")

    # Коло натальної карти
    circle = plt.Circle((0, 0), 1, fill=False, color="#4a0f1f", lw=2)
    ax.add_artist(circle)

    # Зодіакальні знаки по колу (з кольоровими дугами)
    zodiac_signs = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
    zodiac_colors = ["#a83232","#a86f32","#a8a032","#32a832","#32a8a8","#326fa8",
                     "#6f32a8","#a832a8","#a8326f","#3232a8","#32a86f","#6fa832"]
    for i, sign in enumerate(zodiac_signs):
        start_angle = 360/12 * i
        end_angle = start_angle + 360/12
        theta1, theta2 = start_angle, end_angle
        wedge = plt.matplotlib.patches.Wedge(center=(0,0), r=1.05, theta1=theta1, theta2=theta2,
                                             width=0.05, facecolor=zodiac_colors[i], alpha=0.3)
        ax.add_artist(wedge)

        angle_rad = math.radians((theta1+theta2)/2)
        x = 1.25 * math.cos(angle_rad)  # трохи далі від центру
        y = 1.25 * math.sin(angle_rad)
        ax.text(x, y, sign, fontsize=18, ha="center", va="center", color="white", fontweight="bold")

    # Домів Пласідус
    houses = chart.houses
    for i, house in enumerate(houses):
        angle = math.radians(house.lon)
        x = 1.0 * math.cos(angle)
        y = 1.0 * math.sin(angle)
        ax.text(x, y, str(i+1), fontsize=14, ha="center", va="center", color="#6a1b2c")

    # Планети
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x = 0.8 * math.cos(angle)  # трохи далі від центру
        y = 0.8 * math.sin(angle)
        label = PLANET_SYMBOLS.get(obj.id, obj.id)
        color = PLANET_COLORS.get(obj.id, "#6a1b2c")

        ax.plot(x, y, "o", color=color, markersize=14)
        ax.text(x, y, label, fontsize=16, ha="center", va="center", color=color, fontweight="bold")
        ax.text(x + 0.08, y + 0.08, obj.id, fontsize=10, ha="left", va="bottom", color=color)

    # Асцендент і MC
    asc = next((o for o in chart.objects if o.id=="Asc"), None)
    mc = next((o for o in chart.objects if o.id=="MC"), None)
    if asc:
        angle = math.radians(asc.lon)
        x = 1.05 * math.cos(angle)
        y = 1.05 * math.sin(angle)
        ax.text(x, y, "Asc", fontsize=14, ha="center", va="center", color="white", fontweight="bold")
    if mc:
        angle = math.radians(mc.lon)
        x = 1.05 * math.cos(angle)
        y = 1.05 * math.sin(angle)
        ax.text(x, y, "MC", fontsize=14, ha="center", va="center", color="white", fontweight="bold")

    # Аспекти
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.id == asp["planet1"])
        p2 = next(o for o in chart.objects if o.id == asp["planet2"])
        x1, y1 = 0.8 * math.cos(math.radians(p1.lon)), 0.8 * math.sin(math.radians(p1.lon))
        x2, y2 = 0.8 * math.cos(math.radians(p2.lon)), 0.8 * math.sin(math.radians(p2.lon))
        ax.plot([x1, x2], [y1, y2], color=asp["color"], lw=1.5)

    # Логотип Albireo Daria ♏ у секторі Скорпіона
    scorpio_index = zodiac_signs.index("♏")
    theta1 = 360/12 * scorpio_index
    theta2 = theta1 + 360/12
    angle_rad = math.radians((theta1+theta2)/2)
    x_logo = 1.4 * math.cos(angle_rad)
    y_logo = 1.4 * math.sin(angle_rad)
    ax.text(x_logo, y_logo, "Albireo Daria ♏", fontsize=18, ha="center", va="center",
            color="white", fontweight="bold")

    # Легенди планет та аспектів залишаємо як було
    # ...

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ====================== Генерація карти ======================
@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        name = data.get("name", "Person")
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")

        key = cache_key(name, date_str, time_str, place)
        cache_path = os.path.join(CACHE_DIR, f"{key}.json")
        chart_path = os.path.join(CACHE_DIR, f"{key}.png")

        if os.path.exists(cache_path) and os.path.exists(chart_path):
            with open(cache_path) as f:
                cached_data = json.load(f)
            return jsonify({**cached_data, "chart_url": f"/cache/{key}.png"})

        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400
        lat, lon = location.latitude, location.longitude

        tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        tz = pytz.timezone(tz_str)

        naive_dt = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive_dt)

        offset_hours = local_dt.utcoffset().total_seconds() / 3600

        fdate = Datetime(local_dt.strftime("%Y/%m/%d"),
                         local_dt.strftime("%H:%M"),
                         offset_hours)
        pos = GeoPos(lat, lon)
        chart = Chart(fdate, pos, houses="Placidus")

        aspect_list = compute_aspects(chart)

        os.makedirs(CACHE_DIR, exist_ok=True)
        width = data.get("width", 8)
        height = data.get("height", 8)
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

        chart_url = f"https://albireo-daria-96.fly.dev/cache/{key}.png"

        return jsonify({
            **cache_data,
            "chart_url": chart_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cache/<filename>")
def get_cached_chart(filename):
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)