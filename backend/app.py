import os
import math
import numpy as np
from datetime import datetime as dt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from flatlib.chart import Chart

app = Flask(__name__)
CORS(app)

# --- Функція побудови натальної карти ---
def draw_natal_chart(chart, aspects_list):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis("off")
    
    # --- 1) Кільце зодіаку, ширше в 2 рази ---
    r_inner = 0.7
    r_outer = 1.0
    circle = plt.Circle((0,0), r_outer, color="#f0f0f0", zorder=0)
    ax.add_patch(circle)

    # --- 2) Символи знаків по дузі ---
    zodiac_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    zodiac_names   = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                      "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    for i, sym in enumerate(zodiac_symbols):
        angle = np.deg2rad(30*i + 15)  # центр знака
        ax.text(angle, r_outer - 0.05, sym, fontsize=14, ha='center', va='center', color="#444444", rotation=-30*i-15, rotation_mode='anchor')
        # назва знака по дузі, не перекриває символ
        ax.text(angle, r_outer - 0.15, zodiac_names[i], fontsize=9, ha='center', va='center', color="#444444", rotation=-30*i-15, rotation_mode='anchor')

    # --- 3) Логотип Скорпіона у секторі з перевернутими буквами ---
    scorpio_text = "Albireo Daria"
    scorpio_sector_angle = 7*30  # скорпіон
    start_angle = np.deg2rad(scorpio_sector_angle + 5)
    end_angle   = np.deg2rad(scorpio_sector_angle + 25)
    theta_logo = np.linspace(end_angle, start_angle, len(scorpio_text))  # проти годинникової
    r_logo = 0.85
    for ch, th in zip(scorpio_text, theta_logo):
        ax.text(th, r_logo, ch, fontsize=9, ha='center', va='center', color="#444444", rotation=np.rad2deg(th)+180)

    # --- 4) Планети (просте розміщення на колі) ---
    r_planet = 0.80
    for obj in chart.objects:
        lon = getattr(obj, "lon", getattr(obj, "signlon", None))
        if lon is None:
            continue
        th = np.deg2rad(float(lon)%360)
        ax.text(th, r_planet, getattr(obj, "symbol", "?"), fontsize=12, ha='center', va='center', color="#222222")

    # --- 5) Аспекти — прямі хорди, кольорові ---
    aspect_colors = {
        "Conjunction": "#D62728",
        "Sextile":     "#1F77B4",
        "Square":      "#FF7F0E",
        "Trine":       "#2CA02C",
        "Opposition":  "#9467BD",
    }

    aspects_table = []
    legend_seen = {}
    for asp in aspects_list:
        try:
            p1_id = asp.get("planet1")
            p2_id = asp.get("planet2")
            p1 = next((o for o in chart.objects if getattr(o, "id", None) == p1_id), None)
            p2 = next((o for o in chart.objects if getattr(o, "id", None) == p2_id), None)
            if not p1 or not p2:
                continue
            lon1 = float(getattr(p1,"lon",getattr(p1,"signlon",0))) % 360
            lon2 = float(getattr(p2,"lon",getattr(p2,"signlon",0))) % 360
            x1, y1 = np.cos(np.deg2rad(lon1))*r_planet, np.sin(np.deg2rad(lon1))*r_planet
            x2, y2 = np.cos(np.deg2rad(lon2))*r_planet, np.sin(np.deg2rad(lon2))*r_planet
            ax.plot([x1,x2],[y1,y2], color=aspect_colors.get(asp.get("type"),"#777777"), lw=2.2, alpha=0.95, zorder=10, transform=ax.transData)
            
            def dms_str(x):
                d = int(x)%360
                m = int((x-int(x))*60)
                s = int(((x-int(x))*60-m)*60)
                return f"{d}°{m}'{s}''"
            
            aspects_table.append({
                "planet1": p1_id,
                "lon1": dms_str(lon1),
                "planet2": p2_id,
                "lon2": dms_str(lon2),
                "type": asp.get("type"),
                "angle": asp.get("angle"),
                "angle_dms": asp.get("angle_dms"),
                "color": aspect_colors.get(asp.get("type"),"#777777")
            })
            legend_seen[asp.get("type")] = aspect_colors.get(asp.get("type"),"#777777")
        except Exception:
            continue

    # --- 6) Легенда аспектів під картою ---
    from matplotlib.lines import Line2D
    legend_handles = [Line2D([0],[0], color=c, lw=4) for c in legend_seen.values()]
    legend_labels  = list(legend_seen.keys())
    if legend_handles:
        ax_leg = fig.add_axes([0.05, -0.09, 0.9, 0.06])
        ax_leg.axis("off")
        ax_leg.legend(handles=legend_handles, labels=legend_labels, loc="center", ncol=len(legend_handles), frameon=False)

    # --- 7) Повертаємо зображення та таблицю аспектів ---
    plt.tight_layout()
    img_path = os.path.join("static", "chart.png")
    plt.savefig(img_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return img_path, aspects_table

# --- Flask ендпоінт ---
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    date = data.get("date")
    time = data.get("time")
    place = data.get("place")
    # Створюємо chart через flatlib (спрощено)
    # chart = Chart(...) тут ваш код Flatlib
    chart = data.get("chart_objects")  # тимчасово для тесту
    aspects_list = data.get("aspects_list", [])
    
    img_path, table = draw_natal_chart(chart, aspects_list)
    return jsonify({"chart_url": img_path, "aspects": table})

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)