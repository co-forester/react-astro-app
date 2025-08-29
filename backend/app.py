import os
import math
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import aspects
from flatlib import const

app = Flask(__name__)
CORS(app)

CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# ----- Функції -----
def get_timezone(lat, lon):
    try:
        tz_str = TimezoneFinder().timezone_at(lat=lat, lng=lon)
        if not tz_str:
            tz_str = "UTC"
        return pytz.timezone(tz_str)
    except:
        return pytz.UTC

def get_aspects_json(chart):
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

def draw_aspects(ax, chart):
    objs = chart.objects
    for i, p1 in enumerate(objs):
        for p2 in objs[i + 1:]:
            asp = aspects.getAspect(p1, p2)
            if asp:
                a1 = math.radians(p1.lon)
                a2 = math.radians(p2.lon)
                x1, y1 = 0.9 * math.cos(a1), 0.9 * math.sin(a1)
                x2, y2 = 0.9 * math.cos(a2), 0.9 * math.sin(a2)
                ax.plot([x1, x2], [y1, y2], color="red", lw=0.5)

def draw_chart(chart, filename):
    fig, ax = plt.subplots(figsize=(6,6))
    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.axis("off")

    # Сектори домів
    for house in chart.houses:
        angle_start = math.radians(house.lon)
        ax.plot([0, math.cos(angle_start)], [0, math.sin(angle_start)], color="gray", lw=1)

    # Планети
    for p in chart.objects:
        angle = math.radians(p.lon)
        x, y = 0.8 * math.cos(angle), 0.8 * math.sin(angle)
        ax.plot(x, y, "o", color="blue")
        # Додаємо градуси
        ax.text(x*1.05, y*1.05, f"{p.id} {p.lon:.2f}°", fontsize=8, ha="center", va="center")

    # Аспекти
    draw_aspects(ax, chart)

    # Логотип у центрі
    ax.text(0, 0, "SerGio", fontsize=12, ha="center", va="center", weight="bold", color="darkred")

    plt.savefig(filename)
    plt.close(fig)

# ----- Ендпоінт -----
@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.json
    dt_str = data.get("datetime")          # формат "YYYY-MM-DD HH:MM"
    city = data.get("city")
    country = data.get("country")

    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(f"{city}, {country}")
    if not location:
        return jsonify({"error": "Cannot find location"}), 400

    tz = get_timezone(location.latitude, location.longitude)

    dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    dt_obj = tz.localize(dt_obj)

    chart = Chart(dt_obj, location.latitude, location.longitude, hsys="P")  # Placidus

    filename = f"{CHARTS_DIR}/chart_{dt_obj.strftime('%Y%m%d%H%M')}.png"
    draw_chart(chart, filename)

    # JSON дані
    planets = [{"id": p.id, "lon": round(p.lon,2)} for p in chart.objects]
    aspects_json = get_aspects_json(chart)

    return jsonify({
        "chartUrl": filename,
        "planets": planets,
        "aspects": aspects_json
    })

# ----- Запуск -----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)