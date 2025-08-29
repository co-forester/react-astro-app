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
from flatlib import aspects
from flatlib import const

app = Flask(__name__)
CORS(app)

# --- Допоміжні функції ---
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

def deg_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = round((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

def get_timezone(lat, lon):
    try:
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        if not tz_str:
            tz_str = "UTC"
    except:
        tz_str = "UTC"
    return pytz.timezone(tz_str)

def plot_chart(chart, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis("off")
    fig.patch.set_facecolor("#800000")  # бордовий фон

    # --- Лого в центрі ---
    ax.text(0, 0, "♏", fontsize=40, ha="center", va="center", color="gold")

    # --- Планети та градуси ---
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x, y = 0.8 * math.cos(angle), 0.8 * math.sin(angle)
        ax.plot(x, y, "o", color="cyan", markersize=8)
        ax.text(1.05*x, 1.05*y, f"{obj.id}\n{deg_to_dms(obj.lon)}",
                ha="center", va="center", fontsize=10, color="white")

    # --- Будинки (сектора) ---
    for i in range(12):
        start = math.radians(i * 30)
        end = math.radians((i + 1) * 30)
        ax.plot([0.9*math.cos(start), 0.9*math.cos(start)],
                [0.9*math.sin(start), 0.9*math.sin(start)], color="yellow", lw=2)
        mid_angle = (start + end)/2
        ax.text(1.05*math.cos(mid_angle), 1.05*math.sin(mid_angle),
                f"{i+1}", color="yellow", fontsize=12, ha="center", va="center")

    # --- Аспекти ---
    aspect_list = get_aspects(chart)
    aspect_colors = {
        const.CONJ: "red",
        const.SEXT: "green",
        const.SQUARE: "blue",
        const.TRINE: "orange",
        const.OPP: "purple"
    }
    for asp in aspect_list:
        p1 = chart.get(asp["p1"])
        p2 = chart.get(asp["p2"])
        a1, a2 = math.radians(p1.lon), math.radians(p2.lon)
        x1, y1 = 0.9*math.cos(a1), 0.9*math.sin(a1)
        x2, y2 = 0.9*math.cos(a2), 0.9*math.sin(a2)
        color = aspect_colors.get(asp["type"], "white")
        ax.plot([x1, x2], [y1, y2], color=color, lw=0.8)

    plt.savefig(filename, facecolor=fig.get_facecolor(), dpi=150)
    plt.close()
    return aspect_list

# --- API ---
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    date_str = data.get("date")
    time_str = data.get("time")
    city = data.get("city")

    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(city)
    if not loc:
        return jsonify({"error": "City not found"}), 400

    tz = get_timezone(loc.latitude, loc.longitude)

    dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_obj = tz.localize(dt_obj)

    chart = Chart(dt_obj, loc.latitude, loc.longitude, hsys="P")  # P = Placidus

    aspects_list = plot_chart(chart, "chart.png")

    return jsonify({
        "chart": "/chart.png",
        "aspects": aspects_list,
        "planets": [
            {
                "name": obj.id,
                "lon": round(obj.lon, 4),
                "deg": deg_to_dms(obj.lon)
            } for obj in chart.objects
        ]
    })

@app.route("/chart.png")
def chart_png():
    return send_from_directory(os.getcwd(), "chart.png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)