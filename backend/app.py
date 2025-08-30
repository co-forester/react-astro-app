import os
import math
from datetime import datetime as dt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
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

SIGNS = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон","Стрілець","Козеріг","Водолій","Риби"]
COLORS = plt.cm.tab20.colors  # для секторів домів

def generate_chart_image(chart, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'projection':'polar'})
    ax.set_theta_zero_location("W")  # 0° зліва
    ax.set_theta_direction(-1)       # по годинниковій

    # --- Коло та сектори ---
    for i in range(12):
        start = np.deg2rad(i*30)
        end = np.deg2rad((i+1)*30)
        wedge = Wedge((0,0), 1.0, np.rad2deg(start), np.rad2deg(end), facecolor=COLORS[i%len(COLORS)], alpha=0.2)
        ax.add_patch(wedge)

    # --- Мелкі штрихи кожні 10 градусів ---
    for deg in range(0,360,10):
        rad = np.deg2rad(deg)
        if deg % 30 == 0:
            ax.plot([rad, rad], [0.85, 1.0], color='black', lw=2)
            ax.text(rad, 1.05, str(deg), horizontalalignment='center', verticalalignment='center', fontsize=10)
        else:
            ax.plot([rad, rad], [0.9, 1.0], color='black', lw=1)

    # --- Підписи знаків Зодіаку ---
    for i, sign in enumerate(SIGNS):
        rad = np.deg2rad(i*30 + 15)  # центр знаку
        ax.text(rad, 1.15, sign, horizontalalignment='center', verticalalignment='center', fontsize=12, fontweight='bold')

    # --- Логотип / центр ---
    ax.text(0,0, "ASTRO", horizontalalignment='center', verticalalignment='center', fontsize=14, fontweight='bold', color='darkred')

    ax.set_rticks([])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_ylim(0,1.2)

    # --- Планети ---
    for body in chart.bodies:
        lon = float(body.lon)
        rad = np.deg2rad(lon)
        ax.plot(rad, 0.7, 'o', markersize=10, label=body.id)
        ax.text(rad, 0.65, body.id, horizontalalignment='center', verticalalignment='center', fontsize=10)

    plt.savefig(filename, dpi=300, bbox_inches='tight')
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