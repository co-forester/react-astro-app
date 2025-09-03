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
import numpy as np

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

app = Flask(__name__)
CORS(app)

# --- Константи ---
ZODIAC_SYMBOLS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ZODIAC_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
HOUSE_COLORS = [
    ("#ffcccc", "#800000"), ("#ffe6cc", "#804000"), ("#ffffcc", "#808000"),
    ("#e6ffcc", "#408000"), ("#ccffcc", "#008000"), ("#ccffe6", "#008040"),
    ("#ccffff", "#008080"), ("#cce6ff", "#004080"), ("#ccccff", "#000080"),
    ("#e6ccff", "#400080"), ("#ffccff", "#800080"), ("#ffcce6", "#800040")
]

def to_theta(degrees):
    """Переводим градусы в радианы, с поворотом для matplotlib polar."""
    return np.deg2rad(degrees - 90)

def get_house_lon(chart, house_number):
    """Отримати градус початку дому."""
    try:
        house = chart.getHouse(house_number)
        return house.cusp.lon
    except:
        return None

@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        name_for_center = data.get("name")
        logo_sign = data.get("logo_sign")
        logo_text = data.get("logo_text")
        date_str = data["date"]
        time_str = data["time"]
        place_str = data["place"]

        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place_str)
        if location is None:
            return jsonify({"error": "Location not found"}), 400

        tzf = TimezoneFinder()
        tzname = tzf.timezone_at(lat=location.latitude, lng=location.longitude)
        if tzname is None:
            tzname = "UTC"
        tz = pytz.timezone(tzname)

        dt_obj = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_obj = tz.localize(dt_obj)
        fdate = Datetime(dt_obj.year, dt_obj.month, dt_obj.day,
                         dt_obj.hour, dt_obj.minute, tzname)
        chart = Chart(fdate, GeoPos(location.latitude, location.longitude), hsys="P")

        # --- Малювання карти ---
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylim(0, 1.5)

        # --- 2) Роздільники домів (радіальні лінії) ---
        r_inner = 0.15
        r_outer = 1.05
        for i in range(1, 13):
            cusp = get_house_lon(chart, i)
            if cusp is None:
                continue
            th = to_theta(cusp % 360.0)
            ax.plot([th, th], [r_inner, r_outer], color="#888888", lw=0.9, zorder=2)

        # --- 3) Номери домів ---
        house_number_radius = 0.19
        for i in range(1, 13):
            c1 = get_house_lon(chart, i)
            c2 = get_house_lon(chart, (i % 12) + 1)
            if c1 is None or c2 is None:
                continue
            start = float(c1) % 360.0
            end = float(c2) % 360.0
            span = (end - start) % 360.0
            mid = (start + span / 2.0) % 360.0
            ax.text(to_theta(mid), house_number_radius, str(i),
                    fontsize=10, ha="center", va="center",
                    color="#6a1b2c", fontweight="bold", zorder=7)

        # --- 4) Кільце зодіаку з символами та поділкою градусів ---
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

            # Межі знаків
            ax.plot([to_theta(start), to_theta(start)],
                    [ring_radius_start, ring_radius_start + ring_height + 0.01],
                    color="white", lw=1.2, zorder=4)

            # Символ і назва
            symbol_r = ring_radius_start + ring_height - 0.02
            label_r = ring_radius_start + 0.05

            if ZODIAC_NAMES[i] == logo_sign:
                ax.text(center, label_r, logo_text,
                        fontsize=12, ha="center", va="center",
                        color="#FFD700", fontweight="bold",
                        rotation=mid + 90, rotation_mode="anchor", zorder=6)
            else:
                ax.text(center, symbol_r, sym,
                        fontsize=18, ha="center", va="center",
                        color="#ffffff", fontweight="bold",
                        rotation=mid + 90, rotation_mode="anchor", zorder=6)
                ax.text(center, label_r, ZODIAC_NAMES[i],
                        fontsize=9, ha="center", va="center",
                        color="#ffffff", rotation=mid + 90,
                        rotation_mode="anchor", zorder=5)

            # Поділ градусів кожні 5°
            for deg_mark in range(0, 31, 5):
                theta_deg = to_theta(start + deg_mark)
                r_start = ring_radius_start + 0.01
                r_end = ring_radius_start + (0.02 if deg_mark % 10 == 0 else 0.015)
                ax.plot([theta_deg, theta_deg], [r_start, r_end], color="#faf6f7", lw=1, zorder=2)

        # --- 5) Центральне коло і ім’я (полярно-коректно) ---
        max_name_len = len(str(name_for_center)) if name_for_center else 0
        central_circle_radius = max(0.16, 0.08 + max_name_len * 0.012)
        theta_full = np.linspace(0, 2 * np.pi, 361)
        ax.fill_between(theta_full, 0, central_circle_radius, color="#e9c7cf", alpha=0.97, zorder=9)
        ax.plot(theta_full, [central_circle_radius] * len(theta_full), color="#a05c6a", lw=1.2, zorder=10)
        if name_for_center:
            fontsize = min(14, int(central_circle_radius * 130))
            ax.text(0, 0, name_for_center, color="#800000",
                    ha="center", va="center", fontsize=fontsize,
                    fontweight="bold", zorder=15, clip_on=False)

        # --- Збереження ---
        output_path = os.path.join("charts", "chart.png")
        os.makedirs("charts", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight', transparent=True)
        plt.close(fig)

        return jsonify({"chart": output_path})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)