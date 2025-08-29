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
from flatlib import const, aspects
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

app = Flask(__name__)
CORS(app)

# Директория для збереження PNG
CHART_FILE = "chart.png"

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name:
        return pytz.timezone(tz_name)
    return pytz.UTC

def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = round((deg - d - m / 60) * 3600, 2)
    return f"{d}°{m}'{s}\""

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

def generate_chart(date_str, time_str, city):
    # Геокод
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(city)
    if not location:
        return None, "City not found"
    lat, lon = location.latitude, location.longitude
    tz = get_timezone(lat, lon)

    dt_obj = dt.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    dt_obj = tz.localize(dt_obj)
    fdt = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz.zone)
    pos = GeoPos(lat, lon)
    chart = Chart(fdt, pos)

    # Малювання карти
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor('#4B0000')  # бордовий фон

    # Дома кольори
    house_colors = ['#FF9999','#FFCC99','#FFFF99','#CCFF99','#99FF99','#99FFFF',
                    '#99CCFF','#9999FF','#CC99FF','#FF99FF','#FF99CC','#FF6666']

    for i, house in enumerate(chart.houses):
        start = math.radians(house.lon)
        end = math.radians(chart.houses[i+1].lon if i+1 < 12 else chart.houses[0].lon + 360)
        ax.fill_between([0, math.cos(start), math.cos(end)],
                        [0, math.sin(start), math.sin(end)],
                        color=house_colors[i], alpha=0.3)

    # Планети
    for obj in chart.objects:
        lon = math.radians(obj.lon)
        x, y = 0.8 * math.cos(lon), 0.8 * math.sin(lon)
        ax.plot(x, y, 'o', label=obj.id, markersize=10)
        ax.text(x*1.1, y*1.1, f"{obj.id} {to_dms(obj.lon)}", color='white', fontsize=8, ha='center', va='center')

    # Аспекти
    aspects_list = get_aspects(chart)
    for asp in aspects_list:
        p1 = chart.get(asp['p1'])
        p2 = chart.get(asp['p2'])
        a1 = math.radians(p1.lon)
        a2 = math.radians(p2.lon)
        x1, y1 = 0.9 * math.cos(a1), 0.9 * math.sin(a1)
        x2, y2 = 0.9 * math.cos(a2), 0.9 * math.sin(a2)
        ax.plot([x1, x2], [y1, y2], color="red", lw=0.5)

    # Лого в центр (замість тексту)
    ax.text(0,0,"♏", fontsize=40, color='gold', ha='center', va='center')

    plt.savefig(CHART_FILE, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    return chart, aspects_list

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    date_str = data.get("date")  # формат: "29.08.2025"
    time_str = data.get("time")  # формат: "14:30"
    city = data.get("city")       # наприклад: "Mykolaiv, Ukraine"

    chart, aspects_list = generate_chart(date_str, time_str, city)
    if chart is None:
        return jsonify({"error": aspects_list}), 400

    # Планети з градусами
    planets_data = []
    for obj in chart.objects:
        planets_data.append({
            "name": obj.id,
            "lon": obj.lon,
            "lon_dms": to_dms(obj.lon)
        })

    return jsonify({
        "chart": f"/{CHART_FILE}",
        "planets": planets_data,
        "aspects": aspects_list
    })

@app.route(f"/{CHART_FILE}")
def get_chart_file():
    return send_from_directory(os.getcwd(), CHART_FILE)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)