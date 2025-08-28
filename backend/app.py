import os
import math
import json
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

app = Flask(__name__)
CORS(app)

# -------------------- Збереження / очищення кешу ---------------------
def get_cached_chart(form_data):
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.getmtime(fpath) < (datetime.now() - timedelta(days=30)).timestamp():
            os.remove(fpath)
        else:
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data["name"] == form_data["name"] and \
                       data["date"] == form_data["date"] and \
                       data["time"] == form_data["time"] and \
                       data["place"] == form_data["place"]:
                        return data
                except:
                    pass
    return None

def save_chart_cache(data):
    fname = os.path.join(CACHE_DIR, f'{datetime.now().timestamp()}.json')
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------- Побудова карти ---------------------
def draw_natal_chart(chart, aspects_list, name="Person", save_path="static/chart.png"):
    fig, ax = plt.subplots(figsize=(12,12))
    ax.axis("off")

    # Параметри кола
    R_outer = 1.0
    R_inner = 0.75
    house_colors = ["#fbe4e1","#eafbf0","#f5f3fb","#fef9e7","#f1faff","#fff0f5",
                    "#fdf4e4","#f0fff5","#f9f0ff","#fff4f0","#f0f9ff","#fef0f0"]

    # Домів сектори
    for i, house in enumerate(chart.houses):
        start = math.radians(house.start)
        end = math.radians(house.end)
        wedge = mpatches.Wedge((0,0), R_outer+0.2, math.degrees(start), math.degrees(end),
                                facecolor=house_colors[i%12], edgecolor="white", lw=1, alpha=0.5)
        ax.add_patch(wedge)
        mid_angle = (start+end)/2
        x = (R_outer+0.1)*math.cos(mid_angle)
        y = (R_outer+0.1)*math.sin(mid_angle)
        ax.text(x, y, str(i+1), ha="center", va="center", fontsize=12, color="#4a0f1f")

    # Зодіак
    zodiac_signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sign in enumerate(zodiac_signs):
        angle = 2*math.pi/12 * i
        x = (R_outer+0.25) * math.cos(angle)
        y = (R_outer+0.25) * math.sin(angle)
        ax.text(x, y, sign, fontsize=18, ha="center", va="center", color="white")

    # Логотип у Скорпіоні
    scorpio_index = 7
    angle = 2*math.pi/12 * scorpio_index
    x = (R_outer+0.4) * math.cos(angle)
    y = (R_outer+0.4) * math.sin(angle)
    ax.text(x, y, "Albireo Daria", fontsize=14, ha="center", va="center", color="white", fontweight="bold")

    # Планети
    planet_colors = {
        "Sun":"#FFD700", "Moon":"#C0C0C0", "Mercury":"#FFB347", "Venus":"#FF69B4",
        "Mars":"#FF4500", "Jupiter":"#00BFFF", "Saturn":"#8B4513",
        "North Node":"#32CD32", "South Node":"#FF6347", "Pars Fortuna":"#9370DB"
    }
    for obj in chart.objects:
        angle = math.radians(obj.lon)
        x = R_inner * math.cos(angle)
        y = R_inner * math.sin(angle)
        ax.plot(x, y, "o", color=planet_colors.get(obj.id,"#6a1b2c"), markersize=12)
        ax.text(x, y, obj.id, fontsize=10, ha="center", va="center", color="#4a0f1f")

    # Лінії аспектів
    for asp in aspects_list:
        try:
            p1 = next(o for o in chart.objects if o.id == asp["planet1"])
            p2 = next(o for o in chart.objects if o.id == asp["planet2"])
            x1, y1 = R_inner*math.cos(math.radians(p1.lon)), R_inner*math.sin(math.radians(p1.lon))
            x2, y2 = R_inner*math.cos(math.radians(p2.lon)), R_inner*math.sin(math.radians(p2.lon))
            ax.plot([x1, x2], [y1, y2], color=asp["color"], lw=1)
        except:
            continue

    # Анотації Asc і MC
    asc = chart.getObject("Ascendant")
    mc = chart.getObject("MC")
    x_asc, y_asc = R_outer*math.cos(math.radians(asc.lon)), R_outer*math.sin(math.radians(asc.lon))
    x_mc, y_mc = R_outer*math.cos(math.radians(mc.lon)), R_outer*math.sin(math.radians(mc.lon))
    ax.text(x_asc, y_asc, "Asc", color="#ffffff", fontsize=12, fontweight="bold", ha="center", va="center")
    ax.text(x_mc, y_mc, "MC", color="#ffffff", fontsize=12, fontweight="bold", ha="center", va="center")

    # Градуси
    for deg in range(0,360,10):
        angle = math.radians(deg)
        x = (R_outer+0.35)*math.cos(angle)
        y = (R_outer+0.35)*math.sin(angle)
        ax.text(x, y, str(deg), fontsize=8, ha="center", va="center", color="white")

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# -------------------- Генерація карти ---------------------
@app.route("/generate", methods=["POST"])
def generate():
    form_data = request.json
    cached = get_cached_chart(form_data)
    if cached:
        return jsonify(cached)

    name = form_data["name"]
    date = form_data["date"]
    time = form_data["time"]
    place = form_data["place"]

    # --- Геопозиція та час ---
    lat, lon = 47.0, 31.9  # Mykolaiv як дефолт
    dt_obj = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    fdate = Datetime(date, time, 3)  # +3 UTC
    geo = GeoPos(lat, lon)

    # --- Натальна карта ---
    chart = Chart(fdate, geo, hsys=const.PLACIDUS)
    aspects_list = []  # Ваші аспекти тут, ручні обчислення

    chart_url = "/cache/chart.png"
    draw_natal_chart(chart, aspects_list, name, save_path=f".{chart_url}")

    result = {
        "aspects_json": aspects_list,
        "chart_url": chart_url,
        "date": date,
        "name": name,
        "place": place,
        "time": time,
        "timezone": "Europe/Kyiv"
    }
    save_chart_cache(result)
    return jsonify(result)

# -------------------- Health check ---------------------
@app.route("/health")
def health():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8080)