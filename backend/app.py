import os
import math
import json
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

# --- Ініціалізація ---
geolocator = Nominatim(user_agent="my_app")
tf = TimezoneFinder()

# --- Обчислення аспектів ---
# Замість compute_aspects_manual(chart.objects)
aspect_list = compute_aspects(chart)

# --- Малювання карти ---
# Замість draw_natal_chart(...)
draw_chart(chart, png_cache_path)
# Ініціалізація об'єкта для знаходження часового поясу


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
                
# Генерує MD5-хеш для кешування результатів запиту.
# Використовує комбінацію: ім'я користувача, дата народження, час і місце.
def cache_key(name, date_str, time_str, place):
    raw = f"{name}_{date_str}_{time_str}_{place}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()               

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
    
    unicode_font = "DejaVu Sans"  # для Unicode символів
    plt.rcParams["font.family"] = unicode_font

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

# API: /generate
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()
        data = request.get_json() or {}
        name = data.get("name", data.get("firstName", "Person"))
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")

        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date, time, place (і бажано name)"}), 400

        key = cache_key(name, date_str, time_str, place)
        json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_cache_path = os.path.join(CACHE_DIR, f"{key}.png")

        if os.path.exists(json_cache_path) and os.path.exists(png_cache_path):
            mtime = dt.fromtimestamp(os.path.getmtime(json_cache_path))
            if dt.now() - mtime <= timedelta(days=30):
                with open(json_cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                base_url = request.host_url.rstrip("/")
                cached["chart_url"] = f"{base_url}/cache/{key}.png"
                return jsonify(cached)

        location = geolocator.geocode(place, language="en")
        if not location:
            return jsonify({"error": "Місце не знайдено (геокодер)"}), 400
        lat, lon = location.latitude, location.longitude

        tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        tz = pytz.timezone(tz_str)
        naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive)
        offset_hours = local_dt.utcoffset().total_seconds() / 3600.0

        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        try:
            chart = Chart(fdate, pos, hsys=getattr(const, "HOUSES_PLACIDUS", None) or "Placidus")
        except Exception:
            chart = Chart(fdate, pos)

        aspect_list = compute_aspects_manual(chart.objects)

        try:
            draw_natal_chart(chart, aspect_list, png_cache_path)
        except Exception as e:
            result = {
                "name": name, "date": date_str, "time": time_str,
                "place": place, "timezone": tz_str,
                "aspects_json": aspect_list, "chart_url": None,
                "warning": f"Помилка при малюванні картинки: {e}"
            }
            with open(json_cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return jsonify(result), 200

        base_url = request.host_url.rstrip("/")
        out = {
            "name": name, "date": date_str, "time": time_str,
            "place": place, "timezone": tz_str,
            "aspects_json": aspect_list,
            "chart_url": f"{base_url}/cache/{key}.png"
        }
        with open(json_cache_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))