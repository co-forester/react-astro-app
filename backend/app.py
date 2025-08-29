import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless render
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects

# --- Flask ---
app = Flask(__name__)
CORS(app)

# --- Допоміжні функції ---
def dms(deg_float):
    deg = int(deg_float)
    m_float = (deg_float - deg) * 60
    min_ = int(m_float)
    sec = int((m_float - min_) * 60)
    return f"{deg}°{min_}'{sec}\""

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
                    "orb": round(asp.orb,2)
                })
    return aspect_list

def draw_professional_chart(chart):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_facecolor("#4B0000")
    ax.axis("off")

    # --- Зодіакальний круг ---
    zodiac_colors = [
        "#FF4500", "#FF8C00", "#FFD700", "#ADFF2F", "#32CD32", "#00FA9A",
        "#00CED1", "#1E90FF", "#9370DB", "#FF69B4", "#FF1493", "#C71585"
    ]
    for i in range(12):
        wedge = Wedge(center=(0,0), r=1, theta1=i*30, theta2=(i+1)*30,
                      facecolor=zodiac_colors[i], alpha=0.3)
        ax.add_artist(wedge)
        # Знак
        angle = math.radians((i+0.5)*30)
        x, y = 1.05*math.cos(angle), 1.05*math.sin(angle)
        sign_name = chart.getZodiacSign(i+1)
        ax.text(x, y, sign_name, color="white", fontsize=12, ha="center", va="center")

    # --- Логотип в центрі ---
    ax.text(0, 0, "♏", color="gold", fontsize=30, ha="center", va="center")

    # --- Планети + градуси ---
    for obj in chart.objects:
        lon_rad = math.radians(obj.lon)
        x, y = 0.9 * math.cos(lon_rad), 0.9 * math.sin(lon_rad)
        ax.plot(x, y, "o", color="yellow")
        ax.text(x*1.1, y*1.1, f"{obj.id} {dms(obj.lon)}", color="white", fontsize=8, ha="center", va="center")

    # --- Будинки ---
    for i in range(1,13):
        house = chart.get(f"H{i}")
        angle_rad = math.radians(house.lon)
        x, y = math.cos(angle_rad), math.sin(angle_rad)
        ax.text(x*1.05, y*1.05, f"H{i}", color="cyan", fontsize=10, ha="center", va="center")

    # --- Аспекти ---
    aspect_list = get_aspects(chart)
    for asp in aspect_list:
        p1 = chart.get(asp["p1"])
        p2 = chart.get(asp["p2"])
        a1, a2 = math.radians(p1.lon), math.radians(p2.lon)
        x1, y1 = 0.9*math.cos(a1), 0.9*math.sin(a1)
        x2, y2 = 0.9*math.cos(a2), 0.9*math.sin(a2)
        ax.plot([x1, x2], [y1, y2], color="red", lw=0.5, alpha=0.7)

    # --- Акценти ASC, MC, IC, DSC ---
    accents = ["ASC", "MC", "IC", "DSC"]
    for acc in accents:
        obj = chart.get(acc)
        lon_rad = math.radians(obj.lon)
        x, y = math.cos(lon_rad), math.sin(lon_rad)
        ax.plot(x, y, "s", color="orange", markersize=8)
        ax.text(x*1.1, y*1.1, acc, color="orange", fontsize=9, ha="center", va="center")

    chart_path = "chart.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor="#4B0000")
    plt.close()
    return chart_path, aspect_list

# --- Flask маршрут ---
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    date_str = data.get("date")  # "YYYY-MM-DD"
    time_str = data.get("time")  # "HH:MM"
    place = data.get("place")    # "Місто, Країна"

    # --- Геолокація та таймзона ---
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place)
    if not location:
        return jsonify({"error": "Місто не знайдено"}), 400
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    tz = pytz.timezone(tz_str)

    dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_obj = tz.localize(dt_obj)
    fdt = Datetime(dt_obj.year, dt_obj.month, dt_obj.day,
                   dt_obj.hour, dt_obj.minute, dt_obj.second, tz_str)
    pos = GeoPos(location.latitude, location.longitude)

    chart = Chart(fdt, pos, hsys="P")

    chart_path, aspects_data = draw_professional_chart(chart)

    # --- Повертаємо JSON ---
    response = {
        "chart_image": chart_path,
        "aspects": aspects_data,
        "planets": [
            {"id": obj.id, "lon": obj.lon, "dms": dms(obj.lon)} for obj in chart.objects
        ],
        "houses": [
            {"house": f"H{i}", "lon": chart.get(f"H{i}").lon} for i in range(1,13)
        ]
    }
    return jsonify(response)

# --- Статичний маршрут для картинок ---
@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(".", filename)

# --- Запуск ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)