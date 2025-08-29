import os
import math
import hashlib
from datetime import datetime as dt, timedelta

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

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Авт. очищення кешу
def cleanup_cache():
    now = dt.now()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.isfile(fpath):
            mtime = dt.fromtimestamp(os.path.getmtime(fpath))
            if now - mtime > timedelta(days=30):
                os.remove(fpath)

# Символи та кольори планет
PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "North Node":"☊","South Node":"☋","Ascendant":"ASC","MC":"MC",
    "Pars Fortuna":"⚶"
}
PLANET_COLORS = {
    "Sun":"gold","Moon":"silver","Mercury":"darkgray","Venus":"palevioletred",
    "Mars":"red","Jupiter":"orange","Saturn":"brown",
    "Uranus":"deepskyblue","Neptune":"blue","Pluto":"black",
    "Ascendant":"green","MC":"purple"
}

ASPECTS = {
    "conjunction": (0, "#ccc", 8),
    "opposition": (180, "#4a0f1f", 8),
    "trine": (120, "#d4a5a5", 6),
    "square": (90, "#f59ca9", 6),
    "sextile": (60, "#f7eaea", 4)
}

# Конвертація градусів у DMS
def deg_to_dms(angle):
    d = int(angle)
    m = int((angle - d) * 60)
    s = int(((angle - d) * 60 - m) * 60)
    return f"{d}°{m}'{s}\""

# Обчислення аспектів
def compute_aspects(chart):
    results = []
    objs = [o for o in chart.objects if o.id in PLANET_SYMBOLS]

    for i in range(len(objs)):
        for j in range(i+1, len(objs)):
            p1, p2 = objs[i], objs[j]
            angle = abs(p1.lon - p2.lon)
            if angle > 180:
                angle = 360 - angle
            for asp, (target, color, orb) in ASPECTS.items():
                if abs(angle - target) <= orb:
                    results.append({
                        "planet1": p1.id,
                        "planet1_symbol": PLANET_SYMBOLS.get(p1.id,p1.id),
                        "planet2": p2.id,
                        "planet2_symbol": PLANET_SYMBOLS.get(p2.id,p2.id),
                        "type": asp,
                        "angle": deg_to_dms(angle),
                        "color": color
                    })
    return results

# Малювання карти
def draw_chart(chart, filepath):
    fig, ax = plt.subplots(figsize=(12,12), subplot_kw={"projection":"polar"})
    ax.set_facecolor("white")
    ax.set_theta_direction(-1)
    ax.set_theta_offset(math.pi/2)
    ax.set_xticks([])
    ax.set_yticks([])

    # Сектори домов пастельні
    for i, house in enumerate(chart.houses):
        start = math.radians(house.lon)
        end = math.radians(chart.houses[(i+1)%12].lon)
        ax.barh(1, end-start, left=start, color=plt.cm.Pastel1(i/12), alpha=0.25)

    # Планети
    for o in chart.objects:
        if o.id in PLANET_SYMBOLS:
            angle = math.radians(o.lon)
            ax.scatter(angle,0.9,color=PLANET_COLORS.get(o.id,"black"),s=120,zorder=5)
            ax.text(angle,1.05,f"{PLANET_SYMBOLS[o.id]} {deg_to_dms(o.lon)}",
                    ha="center",va="center",fontsize=12,color=PLANET_COLORS.get(o.id,"black"))

    # Аспекти
    aspects_data = compute_aspects(chart)
    for asp in aspects_data:
        p1 = chart.getObject(asp["planet1"])
        p2 = chart.getObject(asp["planet2"])
        a1,a2 = math.radians(p1.lon),math.radians(p2.lon)
        ax.plot([a1,a2],[0.9,0.9],color=asp["color"],lw=1.5,alpha=0.7)

    # Логотип у секторі Скорпіона
    scorpio_start = math.radians(210)
    ax.text(scorpio_start,1.15,"Albireo Daria ♏",
            ha="center",va="center",fontsize=14,color="white",
            bbox=dict(boxstyle="round,pad=0.5",fc="#6a1b2c",ec="none"))

    plt.savefig(filepath,bbox_inches="tight")
    plt.close(fig)

# API
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()
        data = request.json
        name, date, time, place = data["name"], data["date"], data["time"], data["place"]

        # Геолокація
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error":"Місце не знайдено"}),400

        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=location.latitude,lng=location.longitude) or "UTC"
        tz = pytz.timezone(tz_str)

        dt_local = tz.localize(dt.strptime(f"{date} {time}","%Y-%m-%d %H:%M"))
        fdate = Datetime(dt_local.strftime("%Y/%m/%d"),dt_local.strftime("%H:%M"),
                         dt_local.utcoffset().total_seconds()/3600)
        pos = GeoPos(location.latitude,location.longitude)
        chart = Chart(fdate,pos,hsys=const.HOUSES_PLACIDUS)

        # Кеш
        key = f"{name}_{date}_{time}_{place}"
        filehash = hashlib.md5(key.encode()).hexdigest()
        filepath = os.path.join(CACHE_DIR,f"{filehash}.png")
        if not os.path.exists(filepath):
            draw_chart(chart,filepath)

        return jsonify({
            "name":name,"date":date,"time":time,"place":place,"timezone":tz_str,
            "chart_url":f"/cache/{filehash}.png",
            "aspects_json":compute_aspects(chart)
        })
    except Exception as e:
        import traceback
        return jsonify({"error":str(e),"trace":traceback.format_exc()}),500

@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)