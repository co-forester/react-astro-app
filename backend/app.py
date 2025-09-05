import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

# --- Конфіг ---
PLANET_COLORS = {
    "Sun": "#FFCC33", "Moon": "#999999", "Mercury": "#FF6666",
    "Venus": "#FF33CC", "Mars": "#FF0000", "Jupiter": "#6600FF",
    "Saturn": "#333333", "Uranus": "#00FFFF", "Neptune": "#3333FF",
    "Pluto": "#993399", "True Node": "#00FF00", "South Node": "#00FF00",
    "Pars Fortuna": "#FF9900"
}

PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
    "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "True Node": "☊", "South Node": "☋", "Pars Fortuna": "⚶"
}

ASPECTS_DEF = {
    "conjunction": {"angle": 0, "color": "#FF0000"},
    "sextile": {"angle": 60, "color": "#00FF00"},
    "square": {"angle": 90, "color": "#0000FF"},
    "trine": {"angle": 120, "color": "#FF9900"},
    "opposition": {"angle": 180, "color": "#9900FF"}
}

# --- Flask ---
app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# --- Функції ---
def dms(angle):
    deg = int(angle)
    m = int((angle - deg) * 60)
    s = int(((angle - deg) * 60 - m) * 60)
    return f"{deg}°{m}'{s}\""

def generate_chart(name, date_str, time_str, place):
    try:
        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(place)
        if loc is None:
            raise ValueError("Місце не знайдено")
        tz_str = TimezoneFinder().timezone_at(lng=loc.longitude, lat=loc.latitude)
        if tz_str is None:
            tz_str = "UTC"

        dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_obj = pytz.timezone(tz_str).localize(dt_obj)
        fdt = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz_str)
        chart = Chart(fdt, GeoPos(loc.latitude, loc.longitude), hsys="P")

        # --- Планети ---
        planets_list = []
        planet_positions = {}
        for pid in PLANET_SYMBOLS.keys():
            try:
                obj = chart.get(pid)
                angle = obj.lon
                planets_list.append({
                    "name": pid,
                    "symbol": PLANET_SYMBOLS[pid],
                    "lon": angle,
                    "angle_dms": dms(angle)
                })
                planet_positions[pid] = angle
            except Exception:
                continue

        # --- Аспекти ---
        aspect_lines = []
        aspects_table = []
        for i, p1 in enumerate(PLANET_SYMBOLS.keys()):
            for j, p2 in enumerate(PLANET_SYMBOLS.keys()):
                if j <= i:
                    continue
                lon1 = planet_positions.get(p1)
                lon2 = planet_positions.get(p2)
                if lon1 is None or lon2 is None:
                    continue
                diff = abs(lon1 - lon2)
                diff = diff if diff <= 180 else 360 - diff
                for asp_name, cfg in ASPECTS_DEF.items():
                    if abs(diff - cfg["angle"]) <= 1:
                        aspect_lines.append({
                            "planet1": p1,
                            "planet1_symbol": PLANET_SYMBOLS[p1],
                            "planet2": p2,
                            "planet2_symbol": PLANET_SYMBOLS[p2],
                            "type": asp_name,
                            "angle_dms": dms(diff),
                            "color": cfg["color"]
                        })
                        aspects_table.append([p1, p2, asp_name, round(diff, 2)])

        # --- Малювання ---
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
        ax.set_theta_zero_location("S")
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 10)
        ax.axis("off")

        # Зодіак
        for i in range(12):
            start = math.radians(i * 30)
            end = math.radians((i + 1) * 30)
            ax.fill_between([start, end], 0, 10, color=f"C{i}", alpha=0.1)

        # Домів сектори (12)
        for i in range(12):
            start = math.radians(i * 30)
            end = math.radians((i + 1) * 30)
            ax.fill_between([start, end], 0, 10, color=f"C{i}", alpha=0.2)
            ax.text((start + end)/2, 10.5, str(i+1), color="black", fontsize=10,
                    ha="center", va="center")

        # Планети
        for p in planets_list:
            theta = math.radians(p["lon"])
            ax.plot(theta, 8, "o", color=PLANET_COLORS[p["name"]], markersize=12)
            ax.text(theta, 8.5, p["symbol"], color=PLANET_COLORS[p["name"]],
                    ha="center", va="center", fontsize=12)

        # ASC/MC/DSC/IC
        angles = {
            "ASC": chart.get(const.ASC).lon,
            "MC": chart.get(const.MC).lon,
            "DSC": (chart.get(const.ASC).lon + 180) % 360,
            "IC": (chart.get(const.MC).lon + 180) % 360
        }
        for name2, lon in angles.items():
            theta = math.radians(lon)
            ax.text(theta, 11, name2, color="yellow", fontsize=12,
                    ha="center", va="center", fontweight="bold")

        # Аспекти прямими хордами
        for asp in aspect_lines:
            lon1 = math.radians(planet_positions[asp["planet1"]])
            lon2 = math.radians(planet_positions[asp["planet2"]])
            ax.plot([lon1, lon2], [8, 8], color=asp["color"], lw=2)

        # Легенда
        legend_elements = []
        for pid, sym in PLANET_SYMBOLS.items():
            if pid in PLANET_COLORS:
                legend_elements.append(Line2D([0], [0], marker='o', color='w',
                                              markerfacecolor=PLANET_COLORS[pid],
                                              label=f"{sym} {pid}", markersize=10))
        for asp_name, cfg in ASPECTS_DEF.items():
            legend_elements.append(Line2D([0], [0], color=cfg["color"], lw=2.5,
                                          label=asp_name.capitalize()))
        ax.legend(handles=legend_elements, loc="upper center",
                  bbox_to_anchor=(0.5, -0.18),
                  fontsize=12, ncol=3, frameon=False)

        # Центральний логотип
        ax.text(0, 0, name, ha="center", va="center", fontsize=14, fontweight="bold")

        key = hashlib.md5(f"{name}{date_str}{time_str}{place}".encode()).hexdigest()
        png_path = os.path.join(CACHE_DIR, f"{key}.png")
        json_path = os.path.join(CACHE_DIR, f"{key}.json")
        fig.savefig(png_path, bbox_inches="tight", dpi=150)
        plt.close(fig)

        # JSON
        out = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "planets": planets_list,
            "aspects_json": aspect_lines,
            "aspects_table": aspects_table,
            "chart_url": f"{request.host_url.rstrip('/')}/{CACHE_DIR}/{key}.png"
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return jsonify(out)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Ендпоінт ---
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    return generate_chart(data.get("name"), data.get("date"), data.get("time"), data.get("place"))

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