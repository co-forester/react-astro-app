import os
import math
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const, aspects, datetime as fldatetime, geopos

# ---------------- Flask ----------------
app = Flask(__name__)
CORS(app)

# Кеш PNG на 30 днів
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = timedelta(days=30)

# ---------------- Допоміжні функції ----------------
def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tz = tf.timezone_at(lng=lon, lat=lat)
    if not tz:
        tz = "UTC"
    return pytz.timezone(tz)

def dms_str(value):
    deg = int(value)
    min_ = int((value - deg) * 60)
    sec = int(((value - deg) * 60 - min_) * 60)
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
                    "orb": round(asp.orb, 2)
                })
    return aspect_list

def draw_chart(chart, filename):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.axis("off")
    fig.patch.set_facecolor("#4B0000")  # бордовий фон

    # Зодіакальні сектора
    for i in range(12):
        theta1 = math.radians(i*30)
        theta2 = math.radians((i+1)*30)
        ax.fill_between(
            [0, math.cos(theta1), math.cos(theta2)],
            [0, math.sin(theta1), math.sin(theta2)],
            color=f"#{(i*20+100):02x}{(50+i*10):02x}{(150-i*10):02x}", alpha=0.2
        )

    # Логотип у центрі
    ax.text(0,0,"♏", fontsize=30, ha="center", va="center", color="gold")

    # Планети
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        r = 0.85
        x, y = r*math.cos(angle), r*math.sin(angle)
        ax.plot(x, y, 'o', color="yellow")
        ax.text(x*1.05, y*1.05, f"{obj.id} {dms_str(obj.lon)}", color="white", fontsize=8)

    # Доми
    for house in chart.houses:
        angle = math.radians(house.lon)
        r = 0.95
        x, y = r*math.cos(angle), r*math.sin(angle)
        ax.text(x, y, f"H{house.id}", color="cyan", fontsize=8, ha="center", va="center")

    # Аспекти
    aspect_list = get_aspects(chart)
    for asp in aspect_list:
        p1 = chart.get(asp["p1"])
        p2 = chart.get(asp["p2"])
        a1 = math.radians(p1.lon)
        a2 = math.radians(p2.lon)
        x1, y1 = 0.85 * math.cos(a1), 0.85 * math.sin(a1)
        x2, y2 = 0.85 * math.cos(a2), 0.85 * math.sin(a2)
        color = {"CONJUNCTION":"red","SQUARE":"blue","TRINE":"green","OPPOSITION":"purple","SEXTILE":"orange"}.get(asp["type"], "white")
        ax.plot([x1,x2],[y1,y2], color=color, lw=0.7)

    plt.savefig(filename, facecolor=fig.get_facecolor(), dpi=150)
    plt.close()
    return aspect_list

# ---------------- Routes ----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    dt_str = f"{data['date']} {data['time']}"
    city = data["city"]

    # Геолокація
    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(city)
    if not loc:
        return jsonify({"error":"City not found"}), 404
    tz = get_timezone(loc.latitude, loc.longitude)
    naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    local_dt = tz.localize(naive_dt)
    fldt = fldatetime.FDatetime(local_dt.year, local_dt.month, local_dt.day, local_dt.hour, local_dt.minute, 0, tz.zone)

    pos = geopos.GeoPos(loc.latitude, loc.longitude)
    chart = Chart(fldt, pos, const.PLACIDUS)

    # Файл кешу
    cache_file = os.path.join(CACHE_DIR, f"chart_{data['date']}_{data['time']}_{city.replace(' ','_')}.png")
    # Генерація PNG якщо немає або прострочено
    if not os.path.exists(cache_file) or datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file)) > CACHE_TTL:
        aspects_list = draw_chart(chart, cache_file)
    else:
        aspects_list = get_aspects(chart)

    response = {
        "chart_url": f"/chart/{os.path.basename(cache_file)}",
        "planets": [{"id":obj.id, "lon":dms_str(obj.lon)} for obj in chart.objects],
        "houses": [{"id":h.id, "lon":dms_str(h.lon)} for h in chart.houses],
        "aspects": aspects_list
    }
    return jsonify(response)

@app.route("/chart/<filename>")
def serve_chart(filename):
    return send_from_directory(CACHE_DIR, filename)

# ---------------- Main ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)