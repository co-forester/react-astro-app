# app.py — робоча, обережна та сумісна версія
import os
import math
import json
import time
import hashlib
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# optional interactive cursor (if installed)
try:
    import mplcursors
    HAS_MPLCURSORS = True
except Exception:
    HAS_MPLCURSORS = False

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# flatlib
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
# const and aspects usage – будемо використовувати мінімально, вручну обчислюємо аспекти
from flatlib import const

app = Flask(__name__)
CORS(app)

# Кеш
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Очистка кешу старше 30 днів
def cleanup_cache(days: int = 30):
    now_ts = time.time()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.isfile(fpath):
            if now_ts - os.path.getmtime(fpath) > days * 24 * 3600:
                try:
                    os.remove(fpath)
                except Exception:
                    pass

# Викликаємо на старті
cleanup_cache()

# Геокодер + timezone finder (реюзимо інстанси)
geolocator = Nominatim(user_agent="astro_app_v1")
tf = TimezoneFinder()

# Кольори аспектів
ASPECTS_DEF = {
    "conjunction": {"angle": 0, "orb": 8, "color": "#cccccc"},
    "sextile": {"angle": 60, "orb": 6, "color": "#f7eaea"},
    "square": {"angle": 90, "orb": 6, "color": "#8b8b8b"},
    "trine": {"angle": 120, "orb": 8, "color": "#d4a5a5"},
    "opposition": {"angle": 180, "orb": 8, "color": "#4a0f1f"},
}

# Символи планет / імена, кольори
PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆",
    "Pluto": "♇", "North Node": "☊", "South Node": "☋",
    "Ascendant": "ASC", "MC": "MC", "Pars Fortuna": "⚶", "Syzygy": "☌"
}
PLANET_COLORS = {
    "Sun": "gold", "Moon": "silver", "Mercury": "darkorange", "Venus": "deeppink",
    "Mars": "red", "Jupiter": "royalblue", "Saturn": "brown", "Uranus": "deepskyblue",
    "Neptune": "mediumslateblue", "Pluto": "purple", "Ascendant": "green", "MC": "black"
}

# Допоміжні функції
def cache_key(name, date_str, time_str, place):
    key = f"{name}|{date_str}|{time_str}|{place}"
    return hashlib.md5(key.encode()).hexdigest()

def decdeg_to_dms(deg):
    """Перетворює десяткові градуси в (deg, min, sec)"""
    sign = 1 if deg >= 0 else -1
    deg_abs = abs(deg)
    d = int(deg_abs)
    m = int((deg_abs - d) * 60)
    s = round((deg_abs - d - m/60) * 3600, 2)
    d = d * sign
    return d, m, s

def deg_to_str_dms(deg):
    d, m, s = decdeg_to_dms(deg)
    return f"{d}°{m:02d}'{int(s):02d}\""

# Обчислення аспектів вручну (по довготам)
def compute_aspects_manual(objects):
    results = []
    objs = [o for o in objects if hasattr(o, "lon") and hasattr(o, "id")]
    for i in range(len(objs)):
        for j in range(i+1, len(objs)):
            p1 = objs[i]; p2 = objs[j]
            a1 = p1.lon % 360
            a2 = p2.lon % 360
            diff = abs(a1 - a2)
            if diff > 180:
                diff = 360 - diff
            for name, cfg in ASPECTS_DEF.items():
                target = cfg["angle"]
                orb = cfg["orb"]
                if abs(diff - target) <= orb:
                    results.append({
                        "planet1": getattr(p1, "id", str(p1)),
                        "planet1_symbol": PLANET_SYMBOLS.get(getattr(p1, "id", ""), getattr(p1, "id", "")),
                        "planet2": getattr(p2, "id", str(p2)),
                        "planet2_symbol": PLANET_SYMBOLS.get(getattr(p2, "id", ""), getattr(p2, "id", "")),
                        "type": name,
                        "angle": round(diff, 2),
                        "color": cfg["color"]
                    })
                    break
    return results

# Малюємо натальну карту
def draw_natal_chart(chart, aspects_list, save_path, logo_text="Albireo Daria ♏"):
    figsize = (12, 12)
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111, polar=True)
    ax.set_theta_direction(-1)
    ax.set_theta_offset(math.pi/2)
    ax.set_ylim(0, 1.4)
    ax.set_xticks([]); ax.set_yticks([])
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    unicode_font = "DejaVu Sans"  # для Unicode символів

    # --- Сектори будинків у пастельних тонах ---
    house_colors = [
        "#ffe5e5", "#fff0cc", "#e6ffe6", "#e6f0ff", "#f9e6ff", "#e6ffff",
        "#fff5e6", "#f0f0f0", "#ffe6f0", "#e6ffe6", "#e6f0ff", "#fff0e6"
    ]
    try:
        for i in range(12):
            house = chart.houses[i]
            start_deg = house.lon % 360
            end_deg = chart.houses[(i+1)%12].lon % 360
            if end_deg <= start_deg:
                end_deg += 360
            theta_start = math.radians(90 - start_deg)
            theta_end = math.radians(90 - end_deg)
            ax.bar(x=(theta_start+theta_end)/2, height=1.4, width=abs(theta_end-theta_start),
                   bottom=0, color=house_colors[i], edgecolor="none", linewidth=0, alpha=0.3, zorder=0)
    except Exception:
        pass  # якщо будинки не обчислилися, не малюємо

    # --- Знаки зодіаку ---
    zodiac_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    for i, sym in enumerate(zodiac_symbols):
        center_deg = (i * 30) + 15
        theta = math.radians(90 - center_deg)
        r = 1.22
        ax.text(theta, r, sym, fontsize=22, ha="center", va="center",
                color="#6a1b2c", fontfamily=unicode_font, fontweight="bold")

        # --- Градуйровка для знаку (0–30°) ---
        for deg_mark in range(0, 31, 5):
            theta_deg = i*30 + deg_mark
            theta_rad = math.radians(90 - theta_deg)
            r_start = 1.15
            r_end = 1.18 if deg_mark % 10 == 0 else 1.16
            ax.plot([theta_rad, theta_rad], [r_start, r_end], color="#6a1b2c", lw=1)

    # --- Планети ---
    for obj in chart.objects:
        if hasattr(obj, "lon") and hasattr(obj, "id"):
            angle_deg = obj.lon % 360
            theta = math.radians(90 - angle_deg)
            r = 0.95
            symbol = PLANET_SYMBOLS.get(getattr(obj, "id", ""), "?")
            color = PLANET_COLORS.get(getattr(obj, "id", ""), "black")
            ax.text(theta, r, symbol, fontsize=16, ha="center", va="center",
                    color=color, fontfamily=unicode_font)

    # --- Аспекти ---
    for asp in aspects_list:
        try:
            p1 = next(o for o in chart.objects if getattr(o, "id", None) == asp["planet1"])
            p2 = next(o for o in chart.objects if getattr(o, "id", None) == asp["planet2"])
            angle1 = p1.lon % 360
            angle2 = p2.lon % 360
            theta1 = math.radians(90 - angle1)
            theta2 = math.radians(90 - angle2)
            ax.plot([theta1, theta2], [0.95, 0.95], color=asp["color"], linewidth=1.2, zorder=1)
        except Exception:
            continue

    # --- Логотип ---
    try:
        sc_center_deg = 210
        sc_theta = math.radians(90 - sc_center_deg)
        ax.text(sc_theta, 1.27, logo_text, fontsize=14, ha="center", va="center",
                color="white", fontfamily=unicode_font, fontweight="bold",
                bbox=dict(facecolor="#6a1b2c", edgecolor="none", pad=5, boxstyle="round,pad=0.4"), zorder=6)
    except Exception:
        pass

    try:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    finally:
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