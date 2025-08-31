import os
import math
import numpy as np
from datetime import datetime as dt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge
from matplotlib.text import TextPath
from matplotlib.transforms import Affine2D
from matplotlib.font_manager import FontProperties

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from flatlib.chart import Chart

app = Flask(__name__)
CORS(app)

# --- Константи для графіки ---
R_PLANET = 0.80
R_HOUSES = 0.90
ASPECT_COLORS = {
    "Conjunction": "#D62728",
    "Sextile":     "#1F77B4",
    "Square":      "#FF7F0E",
    "Trine":       "#2CA02C",
    "Opposition":  "#9467BD",
}

ZODIAC_SIGNS = [
    ("Aries", "♈"), ("Taurus", "♉"), ("Gemini", "♊"), ("Cancer", "♋"),
    ("Leo", "♌"), ("Virgo", "♍"), ("Libra", "♎"), ("Scorpio", "♏"),
    ("Sagittarius", "♐"), ("Capricorn", "♑"), ("Aquarius", "♒"), ("Pisces", "♓")
]

# --- Допоміжні функції ---
def dms_str(x):
    d = int(x) % 360
    m = int((x - int(x)) * 60)
    s = int(((x - int(x)) * 60 - m) * 60)
    return f"{d}°{m}'{s}''"

def draw_text_on_arc(ax, text, radius, start_angle, clockwise=True, fontsize=12, fontname="DejaVu Sans"):
    """Розміщує текст по дузі. Кожна буква окремо"""
    fp = FontProperties(fname=None, family=fontname)
    theta_sign = -1 if clockwise else 1
    angle_rad = np.deg2rad(start_angle)
    for ch in text:
        tpath = TextPath((0, 0), ch, size=fontsize, prop=fp)
        rot = Affine2D().rotate(angle_rad - np.pi/2)
        tr = rot + Affine2D().translate(radius * np.cos(angle_rad), radius * np.sin(angle_rad)) + ax.transData
        patch = plt.PathPatch(tpath, transform=tr, color='black')
        ax.add_patch(patch)
        angle_rad += theta_sign * fontsize / radius  # регулюємо крок

# --- Маршрут генерації карти ---
@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.json
    date_str = data.get("date")
    time_str = data.get("time")
    place = data.get("place")
    aspects_list = data.get("aspects", [])

    # --- Геокодування та таймзона ---
    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(place)
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
    tz = pytz.timezone(tz_name)
    dt_utc = tz.localize(dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")).astimezone(pytz.UTC)

    chart = Chart(dt_utc, loc.latitude, loc.longitude, hsys='P')

    # --- Створюємо фігуру ---
    fig, ax = plt.subplots(figsize=(10,10), subplot_kw={'polar':True})
    ax.set_ylim(0,1.2)
    ax.axis('off')

    # --- Коло зодіаку (ширше) ---
    for i, (name, symbol) in enumerate(ZODIAC_SIGNS):
        start = i * 30
        end = (i+1) * 30
        wedge = Wedge((0,0), 1.1, start, end, width=0.1, facecolor="#f5f5f5", edgecolor="black", lw=1.5)
        ax.add_patch(wedge)
        # Назва знаку по дузі
        mid_angle = (start + end)/2
        draw_text_on_arc(ax, name, radius=1.05, start_angle=mid_angle, clockwise=False, fontsize=10)
        # Символ знаку ближче до центру
        draw_text_on_arc(ax, symbol, radius=1.0, start_angle=mid_angle, clockwise=False, fontsize=18)

    # --- Коло домів ближче до градусів ---
    for i in range(12):
        angle = np.deg2rad(i*30)
        ax.plot([angle, angle], [0, R_HOUSES], color="gray", lw=1.2, zorder=5)

    # --- Планети (хорди аспектів) ---
    aspects_table = []
    legend_seen = {}
    for asp in aspects_list:
        p1 = next((o for o in chart.objects if getattr(o, "id", None)==asp.get("planet1")), None)
        p2 = next((o for o in chart.objects if getattr(o, "id", None)==asp.get("planet2")), None)
        if not p1 or not p2:
            continue
        lon1 = float(getattr(p1, "lon", getattr(p1, "signlon", 0))) % 360
        lon2 = float(getattr(p2, "lon", getattr(p2, "signlon", 0))) % 360
        th1, th2 = np.deg2rad(lon1), np.deg2rad(lon2)
        # Пряма лінія (хорда)
        ax.plot([th1, th2], [R_PLANET, R_PLANET],
                color=ASPECT_COLORS.get(asp.get("type"), "#777777"),
                lw=2.2, alpha=0.95, zorder=10)
        aspects_table.append({
            "planet1": asp.get("planet1"),
            "lon1": dms_str(lon1),
            "planet2": asp.get("planet2"),
            "lon2": dms_str(lon2),
            "type": asp.get("type"),
            "angle": asp.get("angle"),
            "angle_dms": asp.get("angle_dms"),
            "color": ASPECT_COLORS.get(asp.get("type"), "#777777")
        })
        legend_seen[asp.get("type")] = ASPECT_COLORS.get(asp.get("type"), "#777777")

    # --- Легенда аспектів під картою ---
    if legend_seen:
        ax_leg = fig.add_axes([0.05, -0.09, 0.9, 0.06])
        ax_leg.axis("off")
        legend_handles = [Line2D([0],[0], color=c, lw=4) for c in legend_seen.values()]
        legend_labels = list(legend_seen.keys())
        ax_leg.legend(handles=legend_handles, labels=legend_labels,
                      loc="center", ncol=len(legend_handles), frameon=False)

    # --- Логотип Скорпіона по дузі проти годинникової ---
    scorpio_mid = (7*30 + 15)  # середина сектора Скорпіона
    draw_text_on_arc(ax, "SCORPION", radius=0.85, start_angle=scorpio_mid, clockwise=False, fontsize=12)

    # --- Збереження картинки ---
    chart_path = "/tmp/chart.png"
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    return jsonify({
        "chart_url": "/chart.png",
        "aspects": aspects_table
    })

@app.route("/chart.png")
def serve_chart():
    return send_from_directory("/tmp", "chart.png")

# --- Health ---
@app.route("/health")
def health():
    return "OK", 200

# --- Run ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)