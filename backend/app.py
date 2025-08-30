import os
import math
from datetime import datetime as dt
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

HOUSE_COLORS = [
    "#FFE5B4", "#FFD1DC", "#C1F0F6", "#B9FBC0",
    "#FFFACD", "#E6E6FA", "#FFB6C1", "#D8BFD8",
    "#FFF0F5", "#E0FFFF", "#F5DEB3", "#F0FFF0"
]

PLANET_COLORS = {
    const.SUN: "gold", const.MOON: "silver", const.MERCURY: "gray",
    const.VENUS: "pink", const.MARS: "red", const.JUPITER: "orange",
    const.SATURN: "brown", const.URANUS: "cyan", const.NEPTUNE: "blue",
    const.PLUTO: "purple"
}

ASPECTS = {
    0: ("Conjunction", "red"),
    60: ("Sextile", "green"),
    90: ("Square", "orange"),
    120: ("Trine", "blue"),
    180: ("Opposition", "purple")
}

ASPECT_ORB = 6  # допустимое отклонение градусов

def draw_chart(chart, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar':True})
    ax.set_theta_direction(-1)
    ax.set_theta_offset(math.pi/2)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # --- Сектори домів ---
    for i in range(12):
        start_angle = math.radians(i * 30)
        ax.bar(start_angle, 1, width=math.radians(30), bottom=0, color=HOUSE_COLORS[i], edgecolor="k", alpha=0.3)
        ax.text(start_angle + math.radians(15), 0.9, f"H{i+1}", ha='center', va='center', fontsize=10, fontweight='bold')

    # --- Градуси по колу ---
    for deg in range(0, 360, 10):
        angle = math.radians(deg)
        ax.text(angle, 1.02, f"{deg}°", ha='center', va='center', fontsize=7, rotation=-deg, rotation_mode='anchor')
    
    # --- Логотип/ім'я в центрі ---
    ax.text(0, 0, "ALBIREO", ha='center', va='center', fontsize=16, fontweight='bold', color="darkblue")
    
    # --- Планети ---
    planets = []
    for obj in chart.objects:
        try:
            if obj.isPlanet():
                angle = math.radians(obj.sign * 30 + obj.lon % 30)
                ax.plot(angle, 0.7, 'o', color=PLANET_COLORS.get(obj.name, "black"))
                ax.text(angle, 0.75, obj.name, ha='center', va='center', fontsize=8)
                planets.append((obj, angle))
        except:
            continue

    # --- Аспекти ---
    for i in range(len(planets)):
        for j in range(i+1, len(planets)):
            p1, a1 = planets[i]
            p2, a2 = planets[j]
            lon1 = p1.lon
            lon2 = p2.lon
            diff = abs(lon1 - lon2)
            diff = diff if diff <= 180 else 360 - diff
            for asp_deg, (asp_name, color) in ASPECTS.items():
                if abs(diff - asp_deg) <= ASPECT_ORB:
                    ax.plot([a1, a2], [0.7, 0.7], color=color, linewidth=1, alpha=0.7)

    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close()

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        city = data.get("city")
        date_str = data.get("date")  # 'YYYY-MM-DD'
        time_str = data.get("time")  # 'HH:MM'
        
        # --- Геокодування ---
        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(f"{city}, Ukraine", timeout=5)
        if not loc:
            return jsonify({"error": "Не вдалося знайти місто"}), 400
        pos = GeoPos(loc.latitude, loc.longitude)
        
        # --- Часовий пояс ---
        tz = pytz.timezone(TimezoneFinder().timezone_at(lat=loc.latitude, lng=loc.longitude))
        dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_obj = tz.localize(dt_obj)
        astro_dt = Datetime(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute, tz.zone)
        
        # --- Chart ---
        chart = Chart(astro_dt, pos, hsys="P")
        
        # --- Малюємо ---
        draw_chart(chart)
        return jsonify({"chart": "/chart.png"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chart.png")
def chart_png():
    return send_from_directory(os.getcwd(), "chart.png")

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)