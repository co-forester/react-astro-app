# app.py — професійна натальна карта (Placidus), кеш PNG/JSON,
# дугові підписи, логотип по дузі (♏), DMS, ASC/MC/IC/DSC, хорди аспектів, таблиця аспектів

import os
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from matplotlib.patches import Wedge
import matplotlib.colors as mcolors

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz

import swisseph as swe
from flatlib.chart import Chart
from flatlib import const  # <--- ДОДАНО для точного розрахунку кутів
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# ----------------- Ініціалізація -----------------
EPHE_DIR = os.environ.get("EPHE_DIR", "/ephe")
if not os.path.exists(EPHE_DIR):
    print(f"WARNING: Ефемериди не знайдені за шляхом {EPHE_DIR}")
swe.set_ephe_path(EPHE_DIR)

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
# Змінено TTL кешу на більш практичне значення. Можна винести в змінні середовища.
CACHE_TTL_DAYS = 30

geolocator = Nominatim(user_agent="albireo_astro_app")
tf = TimezoneFinder()

# ----------------- Конфіг -----------------
ZODIAC_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
ZODIAC_NAMES   = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                  "Стрілець","Козеріг","Водолій","Риби"]

HOUSE_COLORS = [
    ("#f9b9b7", "#f28c8c"), ("#f48fb1", "#f06292"), ("#ce93d8", "#ab47bc"), ("#b39ddb", "#7e57c2"),
    ("#9fa8da", "#5c6bc0"), ("#90caf9", "#42a5f5"), ("#81d4fa", "#29b6f6"), ("#80deea", "#26c6da"),
    ("#80cbc4", "#26a69a"), ("#a5d6a7", "#66bb6a"), ("#c5e1a5", "#9ccc65"), ("#e6ee9c", "#d4e157")
]

PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "North Node":"☊","South Node":"☋",
    # "Ascendant":"ASC","MC":"MC",
    "Pars Fortuna":"⚶", "Chiron":"⚷", "Lilith":"⚸", "Ceres":"⚳",
    "Pallas":"⚴", "Juno":"⚵", "Vesta":"⚶"
}
PLANET_COLORS = {
    "Sun":"#f6c90e","Moon":"#c0c0c0","Mercury":"#7d7d7d","Venus":"#e88fb4","Mars":"#e55d5d",
    "Jupiter":"#f3a33c","Saturn":"#b78b68","Uranus":"#69d2e7","Neptune":"#6a9bd1","Pluto":"#3d3d3d",
    "Ascendant":"#2ecc71","MC":"#8e44ad", "Chiron":"#ff66cc", "Lilith":"#993399",
    "Ceres":"#66ff66", "Pallas":"#6699ff", "Juno":"#ffcc33", "Vesta":"#ff9966"
}
PLANETS = [
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
    "Uranus","Neptune","Pluto","Chiron","Lilith","Ceres","Pallas",
    "Juno","Vesta","North Node","South Node"
]
ASPECTS_DEF = {
    "conjunction": {"angle": 0,   "orb": 8, "color": "#D62728"}, "sextile":     {"angle": 60,  "orb": 6, "color": "#1F77B4"},
    "square":      {"angle": 90,  "orb": 6, "color": "#FF7F0E"}, "trine":       {"angle": 120, "orb": 8, "color": "#2CA02C"},
    "opposition":  {"angle": 180, "orb": 8, "color": "#9467BD"}, "semisextile": {"angle": 30,  "orb": 2, "color": "#8C564B"},
    "semisquare":  {"angle": 45,  "orb": 3, "color": "#E377C2"}, "quincunx":    {"angle": 150, "orb": 3, "color": "#7F7F7F"},
    "quintile":    {"angle": 72,  "orb": 2, "color": "#17BECF"}, "biquintile":  {"angle": 144, "orb": 2, "color": "#BCBD22"},
}

# ----------------- Утиліти -----------------
def cleanup_cache(days: int = CACHE_TTL_DAYS):
    now_ts = dt.now().timestamp()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        try:
            if os.path.isfile(fpath):
                if now_ts - os.path.getmtime(fpath) > days * 24 * 3600:
                    os.remove(fpath)
        except Exception:
            pass

def cache_key(name, date_str, time_str, place):
    raw = f"{name}_{date_str}_{time_str}_{place}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
def deg_to_dms(angle_float):
    angle = float(angle_float) % 360.0
    d = int(angle)
    m_f = (angle - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    if s == 60: s = 0; m += 1
    if m == 60: m = 0; d = (d + 1) % 360
    return f"{d}°{m}'{s}\""

def geocode_place(place, retries=2, timeout=8):
    for attempt in range(retries + 1):
        try:
            loc = geolocator.geocode(place, timeout=timeout)
            if loc: return float(loc.latitude), float(loc.longitude)
            if "," not in place and attempt == 0:
                try_place = f"{place}, Ukraine"
                loc2 = geolocator.geocode(try_place, timeout=timeout)
                if loc2: return float(loc2.latitude), float(loc2.longitude)
            return None, None
        except GeocoderTimedOut: continue
        except Exception: break
    return None, None

def safe_house_lon(chart, i, asc_fallback=0.0):
    try:
        v = chart.get_house_cusp(i)
        if v is not None: return float(v) % 360.0
    except Exception: pass
    try:
        asc_val = chart.get(const.ASC).lon
        asc_fallback = float(asc_val) % 360.0
    except Exception: pass
    return (float(asc_fallback) + (i - 1) * 30.0) % 360.0

def compute_aspects_manual(objects, angles):
    results = []
    # Додаємо кутові точки до об'єктів для розрахунку аспектів
    all_objs = list(objects)
    for name, lon in angles.items():
        # Створюємо простий об'єкт-замінник для кутових точок
        angle_obj = type('Angle', (object,), {'id': name, 'lon': lon})()
        all_objs.append(angle_obj)

    objs = [o for o in all_objs if getattr(o, "id", None) and getattr(o, "lon", None) is not None]
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            p1, p2 = objs[i], objs[j]
            a1 = float(getattr(p1, "lon", 0.0))
            a2 = float(getattr(p2, "lon", 0.0))
            diff = abs(a1 - a2)
            if diff > 180: diff = 360 - diff

            for name, cfg in ASPECTS_DEF.items():
                if abs(diff - cfg["angle"]) <= cfg["orb"]:
                    results.append({
                        "planet1": getattr(p1, "id", str(p1)),
                        "planet2": getattr(p2, "id", str(p2)),
                        "type": name,
                        "angle": round(diff, 2),
                        "angle_dms": deg_to_dms(diff),
                        "color": cfg["color"]
                    })
                    break
    return results

# ----------------- Малювання карти -----------------
def draw_natal_chart(chart, aspects_list, save_path, name_for_center=None, logo_text="Albireo Daria", logo_sign="Скорпіон"):
    try:
        # --- Словник конфігурації стилів для легкого налаштування ---
        CHART_STYLE = {
            "font_family": "DejaVu Sans",
            "bg_color": "#4e4247",
            "text_color_light": "#ffffff",
            "text_color_dark": "#6a1b2c",
            "grid_line_color": "#888888",
            "house_sector_inner": 0.15,
            "house_sector_width": 0.25,
            "house_number_radius": 0.19,
            "zodiac_ring_start": 1.10,
            "zodiac_ring_height": 0.20,
            "planet_radius": 0.85,
            "angle_marker_radius": 1.62,
            "angle_arrow_len": 0.07,
            "center_text_color": "#ffaa33"
        }

        fig = plt.figure(figsize=(12, 12))
        ax = plt.subplot(111, polar=True)

        ax.set_theta_zero_location("W"); ax.set_theta_direction(1)
        ax.set_ylim(0, CHART_STYLE["angle_marker_radius"] + 0.15)
        ax.set_xticks([]); ax.set_yticks([])
        fig.patch.set_facecolor(CHART_STYLE["bg_color"])
        ax.set_facecolor(CHART_STYLE["bg_color"])
        plt.rcParams["font.family"] = CHART_STYLE["font_family"]
        ax.set_aspect('equal', 'box'); ax.set_rorigin(-0.02)

        asc_lon = float(chart.get(const.ASC).lon)

        def to_theta(lon):
            return np.deg2rad((float(lon) - asc_lon) % 360.0)
        # --- 1) Сектори будинків (градієнт, ближче до центру) ---
        for i in range(1, 13):
            cusp1 = safe_house_lon(chart, i, asc_lon)
            cusp2 = safe_house_lon(chart, (i % 12) + 1, asc_lon)
            span = (cusp2 - cusp1) % 360.0
            color_start, color_end = HOUSE_COLORS[(i - 1) % 12]
            cmap = mcolors.LinearSegmentedColormap.from_list(f"house{i}_cmap", [color_start, color_end])
            for step in range(24):
                frac1 = step / 24; frac2 = (step + 1) / 24
                angle1 = cusp1 + span * frac1; angle2 = cusp1 + span * frac2
                ax.bar(x=to_theta(angle1), height=CHART_STYLE["house_sector_width"],
                       width=np.deg2rad((angle2 - angle1) % 360.0), bottom=CHART_STYLE["house_sector_inner"],
                       color=cmap(frac1), alpha=0.55, edgecolor=None, align="edge", zorder=1)

        # --- 2) Радіальні лінії (межі домів) ---
        for i in range(1, 13):
            cusp = safe_house_lon(chart, i, asc_lon)
            ax.plot([to_theta(cusp), to_theta(cusp)], [CHART_STYLE["house_sector_inner"], CHART_STYLE["zodiac_ring_start"] - 0.05],
                    color=CHART_STYLE["grid_line_color"], lw=0.9, zorder=2)

        # --- 3) Номери домів (біля центру) ---
        for i in range(1, 13):
            c1 = safe_house_lon(chart, i, asc_lon)
            c2 = safe_house_lon(chart, (i % 12) + 1, asc_lon)
            mid = (c1 + ((c2 - c1) % 360.0) / 2.0) % 360.0
            ax.text(to_theta(mid), CHART_STYLE["house_number_radius"], str(i), fontsize=10, ha="center", va="center",
                    color=CHART_STYLE["text_color_dark"], fontweight="bold", zorder=7)

        # --- 4) Кільце зодіаку ---
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i * 30.0; mid = start + 15.0
            ax.bar(x=to_theta(mid), height=CHART_STYLE["zodiac_ring_height"], width=np.deg2rad(30),
                   bottom=CHART_STYLE["zodiac_ring_start"], color=HOUSE_COLORS[i % 12][0],
                   edgecolor=HOUSE_COLORS[i % 12][1], linewidth=1.2, zorder=3, align='center')
            ax.text(to_theta(mid), CHART_STYLE["zodiac_ring_start"] + CHART_STYLE["zodiac_ring_height"] - 0.02, sym,
                    fontsize=18, ha="center", va="center", color=CHART_STYLE["text_color_light"], fontweight="bold",
                    rotation=(mid - asc_lon + 90) % 360, rotation_mode="anchor", zorder=6)
            ax.text(to_theta(mid), CHART_STYLE["zodiac_ring_start"] + 0.05, ZODIAC_NAMES[i],
                    fontsize=9, ha="center", va="center", color=CHART_STYLE["text_color_light"],
                    rotation=(mid - asc_lon + 90) % 360, rotation_mode="anchor", zorder=5)

        # --- 5) ASC/MC/IC/DSC (маркери та підписи зовні) ---
        try: # 🎯 Основний, точний метод
            angles = {
                "ASC": float(chart.get(const.ASC).lon), "MC": float(chart.get(const.MC).lon),
                "DSC": float(chart.get(const.DESC).lon), "IC": float(chart.get(const.IC).lon)
            }
        except Exception: # 🛡️ Резервний метод
            print("WARNING: Couldn't get precise angles, using manual fallback for DSC/IC.")
            asc = float(chart.get(const.ASC).lon)
            mc = float(chart.get(const.MC).lon)
            angles = {"ASC": asc, "MC": mc, "DSC": (asc + 180) % 360, "IC": (mc + 180) % 360}

        angle_colors = {"ASC": "#00FF00", "DSC": "#FF0000", "MC": "#1E90FF", "IC": "#9400D3"}
        for label, lon in angles.items():
            th = to_theta(lon)
            col = angle_colors[label]
            ax.plot([th], [CHART_STYLE["angle_marker_radius"]], marker="o", markersize=9, color=col, zorder=12)
            ax.annotate("", xy=(th, CHART_STYLE["angle_marker_radius"] - CHART_STYLE["angle_arrow_len"]),
                        xytext=(th, CHART_STYLE["angle_marker_radius"]),
                        arrowprops=dict(facecolor=col, shrink=0.05, width=2, headwidth=8), zorder=12)
            label_text = f"{label} {int(lon % 30)}° {ZODIAC_SYMBOLS[int(lon // 30)]}"
            ax.text(th, CHART_STYLE["angle_marker_radius"] + 0.05, label_text, ha="center", va="center",
                    fontsize=10, color=col, fontweight="bold", zorder=12)

        # --- 6) Планети (всередині) ---
        planet_positions = {}
        for pid in PLANETS:
            obj = chart.get(pid)
            if not obj: continue
            lon = obj.lon; th = to_theta(lon); col = PLANET_COLORS.get(pid, "#ffffff")
            r_planet = CHART_STYLE["planet_radius"]
            ax.plot([th], [r_planet], marker='o', markersize=7, color=col, zorder=12)
            ax.text(th, r_planet + 0.05, PLANET_SYMBOLS[pid], fontsize=18, ha="center", va="center", color=col, zorder=11)
            deg_text = f"{int(lon % 30)}° {ZODIAC_SYMBOLS[int(lon // 30)]}"
            ax.text(th, r_planet - 0.03, deg_text, fontsize=8, ha="center", va="center", color=col,
                    rotation=(np.rad2deg(th) + 90) % 360, rotation_mode="anchor", zorder=11)
            planet_positions[pid] = (th, r_planet)

        # --- 7) Аспекти ---
        for asp in aspects_list:
            p1_id, p2_id = asp["planet1"], asp["planet2"]
            pos1 = planet_positions.get(p1_id) or (to_theta(angles.get(p1_id, 0)), CHART_STYLE["planet_radius"])
            pos2 = planet_positions.get(p2_id) or (to_theta(angles.get(p2_id, 0)), CHART_STYLE["planet_radius"])
            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], color=asp["color"], linewidth=1.5, zorder=5)

        # --- 8) Текст в центрі ---
        ax.text(0, 0, name_for_center or logo_text, fontsize=20, ha="center", va="center",
                color=CHART_STYLE["center_text_color"], zorder=20, fontweight="bold")

        plt.savefig(save_path, dpi=180, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)

    except Exception as e:
        print("Error in draw_natal_chart:", e)
        traceback.print_exc()
        raise

# ----------------- /generate -----------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name", "Person")
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")
        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date (YYYY-MM-DD), time (HH:MM) та place"}), 400

        key = cache_key(name, date_str, time_str, place)
        json_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_path  = os.path.join(CACHE_DIR, f"{key}.png")

        if os.path.exists(json_path) and os.path.exists(png_path):
            base_url = request.host_url.rstrip("/")
            with open(json_path, "r", encoding="utf-8") as f:
                return jsonify({**json.load(f), "chart_url": f"{base_url}/cache/{key}.png"})

        lat, lon = geocode_place(place)
        if lat is None: return jsonify({"error": "Місце не знайдено (геокодер)"}), 400

        tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        tz = pytz.timezone(tz_str)
        naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive)
        offset_hours = local_dt.utcoffset().total_seconds() / 3600.0

        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        
        # HOUSE_SYSTEMS = [const.PLACIDUS, const.WHOLE_SIGN, const.EQUAL, const.KOCH, const.REGIOMONTANUS, const.CAMPANUS, const.TOPOCENTRIC, const.ALCABITIUS, const.MORINUS]
        
        HOUSE_SYSTEMS = ['placidus', 'whole', 'equal', 'koch', 'regiomontanus', 'campanus', 'topocentric', 'alcabitius', 'morinus']

        def create_chart_with_fallback(fdate, pos):
            for hsys in HOUSE_SYSTEMS:
                try:
                    return Chart(fdate, pos, hsys=hsys)
                except Exception as e:
                    
                    print(f"Не вдалося з hsys='{hsys}': {e}")
            raise ValueError("Жодна система домів не спрацювала")
        
            # Спроба створити карту з різними системами домів
        try:
            chart = create_chart_with_fallback(fdate, pos)
        except Exception:
            chart = Chart(fdate, pos)
        
        angles_for_aspects = { 
             "ASC": chart.get(const.ASC).lon, 
             "MC": chart.get(const.MC).lon
        }
    
        try: 
            # Додаємо точні DSC/IC, якщо можливо
            angles_for_aspects["DSC"] = chart.get(const.DESC).lon
            angles_for_aspects["IC"] = chart.get(const.IC).lon
        except Exception: 
            # Резервний варіант
            angles_for_aspects["DSC"] = (angles_for_aspects["ASC"] + 180) % 360
            angles_for_aspects["IC"] = (angles_for_aspects["MC"] + 180) % 360

        aspects_json = compute_aspects_manual(chart.objects, angles_for_aspects)

        draw_natal_chart(chart, aspects_json, png_path, name_for_center=name)

        planets_list = [{"name": p.id, "symbol": PLANET_SYMBOLS.get(p.id, ""), "angle": p.lon} for p in chart.objects if p.id in PLANET_SYMBOLS]
        out = {
            "name": name, "date": date_str, "time": time_str, "place": place, "timezone": tz_str,
            "aspects_table": aspects_json, "planets": planets_list,
            "chart_url": f"{request.host_url.rstrip('/')}/cache/{key}.png"
        }
        with open(json_path, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, indent=2)
        return jsonify(out)
    except Exception as e:
        print("Error in /generate:", e)
        traceback.print_exc()
        return jsonify({"error": "Внутрішня помилка сервера", "message": str(e)}), 500
@app.errorhandler(Exception)
def handle_exception(e):
    print("=== ERROR TRACE ===")
    traceback.print_exc()
    return jsonify({
        "error": "Internal Server Error",
    "message": str(e)
}), 500

@app.route("/cache/<path:filename>")
def cached_file(filename): 
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health(): return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)