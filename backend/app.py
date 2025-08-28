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
def draw_natal_chart(chart, aspects_list, name="Person", save_path="static/chart.png",
                     width=8, height=8):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off")

    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")

    # Визначаємо масштаби залежно від розміру
    font_size_zodiac = max(10, width*2)
    font_size_house = max(8, width*1.5)
    font_size_planet = max(12, width*1.5)
    marker_size = max(8, width*1.5)
    logo_radius = 1.35 * (width/8)

    # Коло карти
    circle = plt.Circle((0,0), 1, fill=False, color="#4a0f1f", lw=2)
    ax.add_artist(circle)

    # Зодіакальні знаки
    zodiac_signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sign in enumerate(zodiac_signs):
        angle = 2*math.pi/12*i
        x, y = 1.1*math.cos(angle), 1.1*math.sin(angle)
        ax.text(x, y, sign, fontsize=font_size_zodiac, ha="center", va="center", color="#f0f0f0")

    # Домів Пласідус
    for i in range(12):
        angle = 2*math.pi/12*i
        x, y = 0.9*math.cos(angle), 0.9*math.sin(angle)
        ax.text(x, y, str(i+1), fontsize=font_size_house, ha="center", va="center", color="#6a1b2c")

    # Планети
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x, y = 0.75*math.cos(angle), 0.75*math.sin(angle)
        label = PLANET_SYMBOLS.get(obj.id, obj.id)
        color = PLANET_COLORS.get(obj.id, "#6a1b2c")
        ax.plot(x, y, "o", color=color, markersize=marker_size)
        ax.text(x, y, label, fontsize=font_size_planet, ha="center", va="center", color=color, fontweight="bold")
        ax.text(x+0.07, y+0.07, obj.id, fontsize=max(7,width), ha="left", va="bottom", color=color)

    # Аспекти
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.id==asp["planet1"])
        p2 = next(o for o in chart.objects if o.id==asp["planet2"])
        x1, y1 = 0.75*math.cos(math.radians(p1.lon)), 0.75*math.sin(math.radians(p1.lon))
        x2, y2 = 0.75*math.cos(math.radians(p2.lon)), 0.75*math.sin(math.radians(p2.lon))
        ax.plot([x1, x2], [y1, y2], color=asp["color"], lw=1.5, zorder=0)

    # Логотип Albireo Daria
    logo_text = "Albireo Daria ♏"
    start_angle, angle_step = 110, 6
    for i, char in enumerate(logo_text):
        theta = math.radians(start_angle - i*angle_step)
        x, y = logo_radius*math.cos(theta), logo_radius*math.sin(theta)
        rotation = start_angle - i*angle_step - 90
        ax.text(x, y, char, fontsize=max(10,width*1.5), ha="center", va="center",
                color="white", fontweight="bold", rotation=rotation)

    # Легенди залишаються як раніше
    ...

    # Легенда планет
    planet_handles, planet_labels = [], []
    for pid, symbol in PLANET_SYMBOLS.items():
        color = PLANET_COLORS.get(pid, "white")
        planet_handles.append(plt.Line2D([0],[0], marker="o", color="w", markerfacecolor=color, markersize=8))
        planet_labels.append(f"{symbol} {pid}")
    legend1 = ax.legend(planet_handles, planet_labels, loc="lower center", bbox_to_anchor=(0.5,-0.18),
                        fontsize=8, ncol=4, frameon=False, title="Планети", title_fontsize=9)
    legend1.get_title().set_color("white")
    for text in legend1.get_texts():
        text.set_color("white")
    ax.add_artist(legend1)

    # Легенда аспектів
    aspect_handles, aspect_labels = [], []
    for atype, color in ASPECT_COLORS.items():
        aspect_handles.append(plt.Line2D([0,1],[0,0], color=color, lw=2))
        aspect_labels.append(atype.capitalize())
    legend2 = ax.legend(aspect_handles, aspect_labels, loc="lower center", bbox_to_anchor=(0.5,-0.28),
                        fontsize=8, ncol=4, frameon=False, title="Аспекти", title_fontsize=9)
    legend2.get_title().set_color("white")
    for text in legend2.get_texts():
        text.set_color("white")
    ax.add_artist(legend2)

    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
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

        return jsonify({**cache_data, "chart_url": f"/cache/{key}.png"})

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