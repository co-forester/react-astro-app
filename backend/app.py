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
from flatlib import aspects, const

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Кольори аспектів
ASPECT_COLORS = {
    "trine": "#d4a5a5",       # світлий бордо
    "square": "#8b8b8b",      # сірий
    "opposition": "#4a0f1f",  # темний бордо
    "sextile": "#f7eaea"      # світлий бордо/білий
}

# ====================== Ключ кешу ======================
def cache_key(name, date, time, place):
    key_str = f"{name}|{date}|{time}|{place}"
    return md5(key_str.encode()).hexdigest()

# ====================== Малюємо натальну карту ======================
def draw_natal_chart(chart, aspects_list, name="Person", save_path="static/chart.png"):
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

    # Домів Пласідус
    for i in range(12):
        angle = 2*math.pi/12 * i
        x = 0.9 * math.cos(angle)
        y = 0.9 * math.sin(angle)
        ax.text(x, y, str(i+1), fontsize=12, ha="center", va="center", color="#4a0f1f")

    # Планети
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x = 0.75 * math.cos(angle)
        y = 0.75 * math.sin(angle)
        ax.plot(x, y, "o", color="#6a1b2c", markersize=10)
        ax.text(x, y, obj.abbrev, fontsize=10, ha="center", va="center", color="#4a0f1f")

    # Аспекти
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.name == asp["planet1"])
        p2 = next(o for o in chart.objects if o.name == asp["planet2"])
        x1, y1 = 0.75*math.cos(math.radians(p1.lon)), 0.75*math.sin(math.radians(p1.lon))
        x2, y2 = 0.75*math.cos(math.radians(p2.lon)), 0.75*math.sin(math.radians(p2.lon))
        ax.plot([x1, x2], [y1, y2], color=asp["color"], lw=1)

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ====================== Аспекти ======================
def compute_aspects(chart):
    aspect_list = []
    for i, p1 in enumerate(chart.objects):
        for j, p2 in enumerate(chart.objects):
            if i >= j:
                continue
            for asp_cls in [aspects.Conjunction, aspects.Sextile, aspects.Square, aspects.Trine, aspects.Opposition]:
                asp = asp_cls(p1, p2)
                if asp.isApplicable():
                    aspect_list.append({
                        "planet1": p1.name,
                        "planet2": p2.name,
                        "type": asp.__class__.__name__.lower(),
                        "color": ASPECT_COLORS.get(asp.__class__.__name__.lower(), "#ccc"),
                        "angle": round(asp.angle, 2)
                    })
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
            return jsonify({
                **cached_data,
                "chart_url": f"/cache/{key}.png"
            })

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

        # Отримуємо зсув від UTC у годинах
        offset_hours = local_dt.utcoffset().total_seconds() / 3600

        # Flatlib datetime (число годин)
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"),
                        local_dt.strftime("%H:%M"),
                        offset_hours)
        pos = GeoPos(lat, lon)
        chart = Chart(fdate, pos, houses="Placidus")

        # Аспекти
        from flatlib import const
        from flatlib import aspects as fl_aspects

        def compute_aspects(chart):
            aspect_list = []
            aspect_types = {
                const.CONJUNCTION: "conjunction",
                const.SEXTILE: "sextile",
                const.SQUARE: "square",
                const.TRINE: "trine",
                const.OPPOSITION: "opposition"
            }

            for i, p1 in enumerate(chart.objects):
                for j, p2 in enumerate(chart.objects):
                    if i >= j:
                        continue
                    asp = fl_aspects.getAspect(p1, p2)
                    if asp:
                        type_str = aspect_types.get(asp.type, "unknown")
                        aspect_list.append({
                            "planet1": p1.id,
                            "planet2": p2.id,
                            "type": type_str,
                            "color": ASPECT_COLORS.get(type_str, "#ccc"),
                            "angle": round(asp.angle, 2)
                        })

            return aspect_list

        # Малюємо карту
        os.makedirs("cache", exist_ok=True)
        draw_natal_chart(chart, aspect_list, name=name, save_path=chart_path)

        # Кешуємо JSON
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

        return jsonify({
            **cache_data,
            "chart_url": f"/cache/{key}.png"
        })

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