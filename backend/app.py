import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects

app = Flask(__name__)
CORS(app)

# --- Функція для округлення градусів з хвилинами і секундами ---
def deg_to_dms(lon):
    deg = int(lon)
    min_float = abs(lon - deg) * 60
    minutes = int(min_float)
    seconds = round((min_float - minutes) * 60, 2)
    return f"{deg}°{minutes}'{seconds}\""

# --- Функція для отримання аспектів ---
def get_aspects(chart):
    aspect_list = []
    objs = chart.objects
    for i, p1 in enumerate(objs):
        for p2 in objs[i + 1:]:
            asp = aspects.getAspect(p1, p2)
            if asp:
                aspect_list.append({
                    "p1": p1.id,
                    "p2": p2.id,
                    "type": asp.type,
                    "orb": round(asp.orb, 2)
                })
    return aspect_list

# --- Головна функція побудови карти ---
def generate_chart(data):
    name = data.get("name", "")
    date = data["date"]
    time = data["time"]
    city = data["city"]
    country = data.get("country", "")

    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(f"{city},{country}")
    lat, lon = location.latitude, location.longitude if location else (0,0)

    tzf = TimezoneFinder()
    timezone_str = tzf.timezone_at(lat=lat, lng=lon) or "UTC"
    tz = pytz.timezone(timezone_str)

    dt_obj = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    dt_obj = tz.localize(dt_obj)

    chart_dt = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz=timezone_str)
    chart = Chart(chart_dt, GeoPos(lat, lon))

    # --- Планети ---
    planets = {}
    for obj in chart.objects:
        planets[obj.id] = {
            "sign": obj.sign,
            "degree": deg_to_dms(obj.lon)
        }

    # --- Аспекти ---
    aspect_list = get_aspects(chart)

    # --- Малюємо карту ---
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis("off")
    circle = plt.Circle((0,0), 1, color="#800000", fill=True)  # бордовий фон
    ax.add_artist(circle)

    # --- Зодіакальні сектори ---
    for i in range(12):
        start = math.radians(i*30)
        end = math.radians((i+1)*30)
        ax.fill_between([0, math.cos(start)], [0, math.sin(start)], [0, math.sin(end)], color=plt.cm.tab20(i), alpha=0.3)

    # --- Логотип у центрі (наприклад, символ Скорпіона) ---
    ax.text(0,0, "♏", fontsize=40, ha='center', va='center', color='gold')

    # --- Планети та підписи ---
    for obj in chart.objects:
        a = math.radians(obj.lon)
        x, y = 0.9 * math.cos(a), 0.9 * math.sin(a)
        ax.plot(x, y, "o", color="yellow")
        ax.text(x*1.05, y*1.05, f"{obj.id}\n{deg_to_dms(obj.lon)}", ha='center', va='center', fontsize=8, color="white")

    # --- Аспекти ---
    for asp in aspect_list:
        p1 = chart.get(asp["p1"])
        p2 = chart.get(asp["p2"])
        a1, a2 = math.radians(p1.lon), math.radians(p2.lon)
        x1, y1 = 0.9 * math.cos(a1), 0.9 * math.sin(a1)
        x2, y2 = 0.9 * math.cos(a2), 0.9 * math.sin(a2)
        ax.plot([x1, x2], [y1, y2], color="red", lw=0.5)

    # --- Зберігаємо PNG ---
    chart_path = os.path.join("charts", "chart.png")
    os.makedirs("charts", exist_ok=True)
    plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor="#800000")
    plt.close(fig)

    return {
        "planets": planets,
        "aspects": aspect_list,
        "chart": chart_path
    }

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        result = generate_chart(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)