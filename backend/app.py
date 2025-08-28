import os
import math
import json
from datetime import datetime as dt, timedelta
from hashlib import md5

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ====================== Кольори ======================
ASPECT_COLORS = {
    "trine": "#d4a5a5",
    "square": "#8b8b8b",
    "opposition": "#4a0f1f",
    "sextile": "#f7eaea",
    "conjunction": "#ccc"
}
PLANET_COLORS = {
    "Sun": "#FFD700",
    "Moon": "#C0C0C0",
    "Mercury": "#FF8C00",
    "Venus": "#FF1493",
    "Mars": "#DC143C",
    "Jupiter": "#1E90FF",
    "Saturn": "#8B4513",
    "Uranus": "#40E0D0",
    "Neptune": "#0000FF",
    "Pluto": "#9400D3",
    "North Node": "#32CD32",
    "South Node": "#228B22",
    "Pars Fortuna": "#FF69B4",
    "Syzygy": "#A9A9A9"
}

# ====================== Ключ кешу ======================
def cache_key(name, date, time, place):
    key_str = f"{name}|{date}|{time}|{place}"
    return md5(key_str.encode()).hexdigest()

# ====================== Малюємо карту ======================
def draw_natal_chart(chart, aspects_list, save_path="cache/chart.png", name="Person"):
    fig, ax = plt.subplots(figsize=(12,12))
    ax.axis("off")

    # Фон кола
    outer_radius = 1.0
    inner_radius = 0.0
    ax.add_artist(plt.Circle((0,0), outer_radius, fill=False, color="#4a0f1f", lw=2))

    # ====================== Дома Placidus ======================
    houses = chart.houses
    for i, house in enumerate(houses):
        start_deg = float(house.lon)
        end_deg = float(houses[(i+1)%12].lon)
        wedge = Wedge(center=(0,0), r=outer_radius, theta1=start_deg, theta2=end_deg,
                      facecolor=f"#{i+1:02x}{i+1:02x}{i+1:02x}", alpha=0.05)
        ax.add_patch(wedge)
        # Підпис номера дому
        mid_angle = math.radians((start_deg+end_deg)/2)
        x = 1.05*math.cos(mid_angle)
        y = 1.05*math.sin(mid_angle)
        ax.text(x, y, str(i+1), ha="center", va="center", fontsize=12, color="#4a0f1f")

    # ====================== Знаки зодіаку ======================
    zodiac_signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sign in enumerate(zodiac_signs):
        angle = 2*math.pi/12*i
        x = 1.15 * math.cos(angle)
        y = 1.15 * math.sin(angle)
        ax.text(x, y, sign, fontsize=16, ha="center", va="center", color="#4a0f1f")

    # ====================== Планети ======================
    for obj in chart.objects:
        angle_rad = math.radians(float(obj.lon))
        x = 0.75 * math.cos(angle_rad)
        y = 0.75 * math.sin(angle_rad)
        ax.plot(x, y, "o", color=PLANET_COLORS.get(obj.id,obj.id), markersize=12)
        ax.text(x, y, obj.id, fontsize=12, ha="center", va="center", color=PLANET_COLORS.get(obj.id,obj.id))

    # ====================== Лінії аспектів ======================
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.id==asp["planet1"])
        p2 = next(o for o in chart.objects if o.id==asp["planet2"])
        x1 = 0.75 * math.cos(math.radians(float(p1.lon)))
        y1 = 0.75 * math.sin(math.radians(float(p1.lon)))
        x2 = 0.75 * math.cos(math.radians(float(p2.lon)))
        y2 = 0.75 * math.sin(math.radians(float(p2.lon)))
        ax.plot([x1,x2],[y1,y2], color=asp["color"], lw=1)

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ====================== Обчислення аспектів ======================
def compute_aspects(chart):
    aspect_list = []
    aspect_types = {
        const.CONJUNCTION: "conjunction",
        const.SEXTILE: "sextile",
        const.SQUARE: "square",
        const.TRINE: "trine",
        const.OPPOSITION: "opposition"
    }
    for i, p1 in enumerate(chart.objects):
        for j, p2 in enumerate(chart.objects):
            if i>=j: continue
            for asp_const in aspect_types:
                asp = aspects.getAspect(p1,p2,asp_const)
                if asp:
                    aspect_list.append({
                        "planet1": p1.id,
                        "planet2": p2.id,
                        "type": aspect_types[asp_const],
                        "color": ASPECT_COLORS.get(aspect_types[asp_const],"#ccc"),
                        "angle": round(asp.angle,2)
                    })
    return aspect_list

# ====================== Генерація карти ======================
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        name = data.get("name")
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")

        # Геокодування
        loc = geolocator.geocode(place)
        if not loc: return jsonify({"error":"Місто не знайдено"}),400
        geo = GeoPos(loc.latitude, loc.longitude)

        # Часовий пояс
        tz_str = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
        local_dt = dt.strptime(f"{date_str} {time_str}","%Y-%m-%d %H:%M")
        offset_hours = local_dt.utcoffset().total_seconds()/3600 if local_dt.utcoffset() else 0
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)

        # Ключ кешу
        key = cache_key(name,date_str,time_str,place)
        chart_path = os.path.join(CACHE_DIR,f"{key}.png")
        cache_path = os.path.join(CACHE_DIR,f"{key}.json")

        # Якщо є кеш <30 днів
        if os.path.exists(cache_path):
            dt_cache = dt.fromtimestamp(os.path.getmtime(cache_path))
            if dt.now()-dt_cache < timedelta(days=30):
                with open(cache_path) as f:
                    cached = json.load(f)
                    return jsonify(cached)

        chart = Chart(fdate, geo, const.PLACIDUS)
        aspect_list = compute_aspects(chart)
        draw_natal_chart(chart, aspect_list, save_path=chart_path, name=name)

        # Збереження кешу
        cache_data = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "aspects_json": aspect_list,
            "chart_url": f"/cache/{key}.png"
        }
        with open(cache_path,"w") as f:
            json.dump(cache_data,f)

        return jsonify(cache_data)

    except Exception as e:
        return jsonify({"error": str(e)}),500

# ====================== Кеш файли ======================
@app.route("/cache/<filename>")
def get_cached_chart(filename):
    return send_from_directory(CACHE_DIR, filename)

# ====================== Health ======================
@app.route("/health")
def health():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)