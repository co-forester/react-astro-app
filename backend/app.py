import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from matplotlib.font_manager import FontProperties

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const

app = Flask(__name__)
CORS(app)

# ----------------- Chart Drawing -----------------
def draw_chart(chart, filename, logo_text="ASTRO"):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis("off")

    # ----------------- Zodiac Signs -----------------
    zodiac_symbols = ["♈", "♉", "♊", "♋", "♌", "♍",
                      "♎", "♏", "♐", "♑", "♒", "♓"]
    for i, symbol in enumerate(zodiac_symbols):
        angle_rad = math.radians(i * 30 + 15)
        ax.text(1.05 * math.cos(angle_rad), 1.05 * math.sin(angle_rad),
                symbol, ha='center', va='center', fontsize=14, fontweight='bold')

    # ----------------- Houses -----------------
    num_houses = 12
    colors = plt.cm.tab20.colors
    for i in range(num_houses):
        start = i * 30
        wedge = Wedge(center=(0, 0), r=1, theta1=start, theta2=start + 30,
                      facecolor=colors[i % len(colors)], alpha=0.2)
        ax.add_patch(wedge)
        angle_rad = math.radians(start + 15)
        ax.text(0.9*math.cos(angle_rad), 0.9*math.sin(angle_rad),
                str(i+1), ha='center', va='center', fontsize=10, fontweight='bold')

    # ----------------- Planets -----------------
    planet_symbols = {
        const.SUN: "☉", const.MOON: "☽", const.MERCURY: "☿", const.VENUS: "♀",
        const.MARS: "♂", const.JUPITER: "♃", const.SATURN: "♄",
        const.URANUS: "♅", const.NEPTUNE: "♆", const.PLUTO: "♇"
    }
    fp = FontProperties(size=20)

    for p in chart.planets:
        deg = float(p.lon)
        angle_rad = math.radians(deg)
        r = 0.7
        ax.text(r*math.cos(angle_rad), r*math.sin(angle_rad),
                planet_symbols.get(p.id, p.id), fontproperties=fp,
                ha='center', va='center', color="black")
        ax.text(0.8*math.cos(angle_rad), 0.8*math.sin(angle_rad),
                f"{int(deg)}°", ha='center', va='center', fontsize=8, color="gray")

    # ----------------- Aspects -----------------
    aspect_colors = {
        "Conjunction": "red", "Sextile": "green", "Square": "orange",
        "Trine": "blue", "Opposition": "purple"
    }
    for a in chart.aspects:
        if a.type in aspect_colors:
            p1 = chart.get(a.p1)
            p2 = chart.get(a.p2)
            angle1 = math.radians(float(p1.lon))
            angle2 = math.radians(float(p2.lon))
            x1, y1 = 0.7*math.cos(angle1), 0.7*math.sin(angle1)
            x2, y2 = 0.7*math.cos(angle2), 0.7*math.sin(angle2)
            ax.plot([x1, x2], [y1, y2], color=aspect_colors[a.type], linewidth=1)

    # ----------------- Logo -----------------
    circle = Circle((0, 0), 0.1, color="lightgray", zorder=10)
    ax.add_patch(circle)
    ax.text(0, 0, logo_text, ha='center', va='center', fontsize=12, fontweight='bold')

    plt.savefig(filename, bbox_inches="tight", dpi=150)
    plt.close()


# ----------------- Generate Chart -----------------
@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.json
    dt_str = data.get("datetime")
    city = data.get("city")
    country = data.get("country")
    logo = data.get("logo", "ASTRO")

    # Geolocation
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(f"{city}, {country}")
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    tz = pytz.timezone(timezone_str)
    dt_obj = dt.strptime(dt_str, "%Y-%m-%d %H:%M")
    dt_utc = tz.localize(dt_obj).astimezone(pytz.utc)

    chart = Chart(dt_utc.strftime("%Y-%m-%d %H:%M"), location.latitude, location.longitude)
    filename = "chart.png"
    draw_chart(chart, filename, logo_text=logo)

    return jsonify({"chart_url": f"/{filename}"})


# ----------------- Serve Chart -----------------
@app.route("/<path:filename>")
def serve_chart(filename):
    return send_from_directory(os.getcwd(), filename)


# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200


# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)