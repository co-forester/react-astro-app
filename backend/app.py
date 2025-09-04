# app.py — професійна натальна карта (Placidus), кеш PNG/JSON, кольори домів, символи, ASC/MC/DSC/IC, Health

import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt
import numpy as np

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const

# ----------------- Конфіг -----------------
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
HOUSE_COLORS = [
    ("#FFCCCC", "#CC6666"), ("#FFE5CC", "#CC9966"), ("#FFFFCC", "#CCCC66"),
    ("#CCFFCC", "#66CC66"), ("#CCFFFF", "#66CCCC"), ("#CCCCFF", "#6666CC"),
    ("#FFCCFF", "#CC66CC"), ("#FFCCCC", "#CC6666"), ("#FFE5CC", "#CC9966"),
    ("#FFFFCC", "#CCCC66"), ("#CCFFCC", "#66CC66"), ("#CCFFFF", "#66CCCC")
]

# ----------------- Flask -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Утиліти -----------------
def to_theta(deg):
    # Перетворення градусів на радіани для полярного графіку (0° = вершина кола)
    return np.deg2rad((90 - deg) % 360)

def cache_filename(key):
    hashed = hashlib.md5(key.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{hashed}.png")

def generate_chart_image(chart_data, filename):
    try:
        fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'polar': True})
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        ax.set_axis_off()

        # --- Кільце зодіаку ---
        ring_radius_start = 1.10
        ring_height = 0.20
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i * 30.0
            end = start + 30.0
            span = (end - start) % 360.0
            mid = (start + span/2.0) % 360.0

            center = to_theta(mid)
            width = np.deg2rad(span)

            ax.bar(
                x=center,
                height=ring_height,
                width=width,
                bottom=ring_radius_start,
                color=HOUSE_COLORS[i % 12][0],
                edgecolor=HOUSE_COLORS[i % 12][1],
                linewidth=1.2,
                zorder=3,
                align='center'
            )

            # Символи зодіаку
            ax.text(
                x=center,
                y=ring_radius_start + ring_height/2,
                s=sym,
                fontsize=14,
                ha='center',
                va='center',
                color='black',
                zorder=5
            )

        # --- ASC/MC/DSC/IC ---
        points = {"ASC": chart_data.get("ASC"), "MC": chart_data.get("MC"),
                  "DSC": chart_data.get("DSC"), "IC": chart_data.get("IC")}
        point_colors = {"ASC":"yellow", "MC":"yellow", "DSC":"yellow", "IC":"yellow"}
        point_radius = 1.35

        for name, deg in points.items():
            if deg is not None:
                theta = to_theta(deg)
                ax.plot([theta], [point_radius], 'o', color=point_colors[name], markersize=10, zorder=6)
                ax.text(theta, point_radius + 0.05, name, color='yellow', ha='center', va='center', fontsize=10)

        fig.tight_layout()
        fig.savefig(filename, dpi=150, bbox_inches='tight', transparent=True)
        plt.close(fig)
        return True
    except Exception as e:
        print("Error generating chart:", e)
        traceback.print_exc()
        return False

def get_chart_data(date_str, time_str, city):
    try:
        dt_str = f"{date_str} {time_str}"
        naive_dt = dt.strptime(dt_str, "%Y-%m-%d %H:%M")
        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(city)
        if loc is None:
            return None, "City not found"
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
        if tz_str is None:
            return None, "Timezone not found"
        tz = pytz.timezone(tz_str)
        aware_dt = tz.localize(naive_dt)
        chart = Chart(aware_dt, loc.latitude, loc.longitude, const.PLACIDUS)
        data = {
            "ASC": float(chart.get(const.ASC).lon),
            "MC": float(chart.get(const.MC).lon),
            "DSC": (float(chart.get(const.ASC).lon) + 180) % 360,
            "IC": (float(chart.get(const.MC).lon) + 180) % 360
        }
        return data, None
    except Exception as e:
        print("Error generating chart data:", e)
        traceback.print_exc()
        return None, str(e)

# ----------------- Endpoints -----------------
@app.route("/generate", methods=["POST"])
def generate():
    req = request.get_json()
    date = req.get("date")
    time = req.get("time")
    city = req.get("city")
    if not date or not time or not city:
        return jsonify({"error": "Missing parameters"}), 400

    key = f"{date}_{time}_{city}"
    png_path = cache_filename(key)

    if not os.path.exists(png_path):
        chart_data, err = get_chart_data(date, time, city)
        if err:
            return jsonify({"error": f"Chart generation failed: {err}"}), 500
        success = generate_chart_image(chart_data, png_path)
        if not success:
            return jsonify({"error": "Chart generation failed"}), 500

<<<<<<< HEAD
    return jsonify({"chart_url": f"/cache/{os.path.basename(png_path)}"})
=======
        lat, lon = geocode_place(place)
        if lat is None:
            return jsonify({"error": "Місце не знайдено (геокодер)"}), 400

        try:
            tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            tz = pytz.timezone(tz_str)
        except Exception:
            tz_str = "UTC"
            tz = pytz.timezone("UTC")

        try:
            naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            local_dt = tz.localize(naive)
            offset_hours = (local_dt.utcoffset().total_seconds() / 3600.0) if local_dt.utcoffset() else 0.0
        except Exception as e:
            return jsonify({"error": f"Невірний формат date/time: {str(e)}"}), 400

        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        try:
            chart = Chart(fdate, pos, hsys='P')
        except Exception:
            chart = Chart(fdate, pos)

        aspects_json = compute_aspects_manual(chart.objects)
        try:
            draw_natal_chart(chart, aspects_json, png_path, name_for_center=name, logo_text="Albireo Daria")
        except Exception as e:
            base_url = request.host_url.rstrip("/")
            out = {
                "name": name, "date": date_str, "time": time_str,
                "place": place, "timezone": tz_str,
                "aspects_json": aspects_json,
                "aspects_table": aspects_json,
                "chart_url": None,
                "warning": f"Помилка при малюванні картинки: {str(e)}"
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            return jsonify(out), 200
        
        # ----------------- Додаємо planets -----------------
        PLANET_SYMBOLS = {
            "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀",
            "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
            "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
        }

        planets_list = []
        for obj in chart.objects:
            pid = getattr(obj, "id", None)
            if pid in PLANET_SYMBOLS:
                planets_list.append({
                    "name": pid,
                    "symbol": PLANET_SYMBOLS[pid],
                    "angle": float(getattr(obj, "lon", 0)) % 360
                })

        def float_to_dms(angle: float):
            deg = int(angle)
            minutes_float = (angle - deg) * 60
            minutes = int(minutes_float)
            seconds = round((minutes_float - minutes) * 60, 1)
            return f"{deg}° {minutes}' {seconds}\""

        aspects_table = []
        for asp in aspects_json:
            aspects_table.append({
                "planet1": asp["planet1"],
                "planet2": asp["planet2"],
                "type": asp["type"],
                "angle": asp["angle"],  # градуси у float
                "angle_dms": float_to_dms(asp["angle"]),  # тепер у DMS
                "color": ASPECTS_DEF.get(asp["type"], {}).get("color", "#777777")
            })

        out = {
            "name": name, "date": date_str, "time": time_str,
            "place": place, "timezone": tz_str,
            "aspects_json": aspects_json,
            "aspects_table": aspects_table,
            "planets": planets_list,  # <-- сюди додано
            "chart_url": f"{request.host_url.rstrip('/')}/cache/{key}.png"
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return jsonify(out), 200

    except Exception as e:
        print("Unhandled error in /generate:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
>>>>>>> b8200be (пусічка)

# ----------------- Статика кешу -----------------
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)