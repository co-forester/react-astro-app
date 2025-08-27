# app.py

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
from flatlib import aspects
from flatlib import const

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

# Папка для кешу
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ====================== Кольори аспектів ======================
ASPECT_COLORS = {
    "trine": "#d4a5a5",       # світлий бордо
    "square": "#8b8b8b",      # сірий
    "opposition": "#4a0f1f",  # темний бордо
    "sextile": "#f7eaea"      # світлий бордо/білий
}

# ====================== Генерація ключа кешу ======================
def cache_key(name, date, time, place):
    key_str = f"{name}|{date}|{time}|{place}"
    return md5(key_str.encode()).hexdigest()

# ====================== Малюємо натальну карту ======================
def draw_natal_chart(chart, name="Person", save_path="static/chart.png"):
    import matplotlib.pyplot as plt
    import math

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.axis("off")

    # Коло натальної карти
    circle = plt.Circle((0, 0), 1, fill=False, color="#4a0f1f", lw=2)
    ax.add_artist(circle)

    # Зодіакальні знаки по колу
    zodiac_signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sign in enumerate(zodiac_signs):
        angle = 2*math.pi/12 * i
        x = 1.05 * math.cos(angle)
        y = 1.05 * math.sin(angle)
        ax.text(x, y, sign, fontsize=14, ha="center", va="center", color="#4a0f1f")

    # Планети
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x = 0.85 * math.cos(angle)
        y = 0.85 * math.sin(angle)
        symbol = const.SYMBOLS.get(obj.name, obj.name)  # коректний символ
        ax.plot(x, y, "o", color="#6a1b2c", markersize=8)
        ax.text(x, y, symbol, fontsize=10, ha="center", va="center", color="#4a0f1f")

    # Домів Пласідус (орієнтовно по колу)
    for i in range(12):
        angle = 2*math.pi/12 * i
        x = 0.9 * math.cos(angle)
        y = 0.9 * math.sin(angle)
        ax.text(x, y, str(i+1), fontsize=10, ha="center", va="center", color="#4a0f1f")

    # Заголовок
    ax.set_title(f"Natal Chart - {name}", fontsize=16)

    # Зберігаємо
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ====================== Генерація аспектів ======================
def compute_aspects(chart):
    aspect_list = []
    planet_names = [obj.name for obj in chart.objects]
    for i, p1 in enumerate(chart.objects):
        for j, p2 in enumerate(chart.objects):
            if i >= j:
                continue
            for aspect in [aspects.Conjunction, aspects.Sextile, aspects.Square, aspects.Trine, aspects.Opposition]:
                asp = aspect(p1, p2)
                if asp.isApplicable():
                    aspect_type = asp.__class__.__name__.lower()
                    aspect_list.append({
                        "planet1": p1.name,
                        "planet2": p2.name,
                        "type": aspect_type,
                        "color": ASPECT_COLORS.get(aspect_type, "#ccc")
                    })
    return aspect_list

# ====================== Генерація карти ======================
@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        name = data.get("name", "Person")
        date_str = data.get("date")   # YYYY-MM-DD
        time_str = data.get("time")   # HH:MM
        place = data.get("place")     # Місто/адреса

        # Перевірка кешу
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

        # Flatlib datetime та позиція
        utc_offset_hours = local_dt.utcoffset().total_seconds() / 3600
        date = Datetime(local_dt.strftime("%Y/%m/%d"),
                 local_dt.strftime("%H:%M"),
                 utc_offset_hours)
        pos = GeoPos(lat, lon)
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"),
                 local_dt.strftime("%H:%M"),
                 utc_offset_hours)
        chart = Chart(fdate, pos, houses="Placidus")  # система домів Пласідус

        # Малюємо карту
        os.makedirs("cache", exist_ok=True)
        draw_natal_chart(chart, name=name, save_path=chart_path)

        # Аспекти
        aspect_list = compute_aspects(chart)

        # Зберігаємо кеш
        cache_data = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "aspects": aspect_list
        }
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)

        return jsonify({
            **cache_data,
            "chart_url": f"/cache/{key}.png"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================== Віддача файлів кешу ======================
@app.route("/cache/<filename>")
def get_cached_chart(filename):
    return send_from_directory(CACHE_DIR, filename)

# ====================== Health ======================
@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)