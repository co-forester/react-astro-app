# app.py — професійна натальна карта (Placidus), кеш PNG/JSON,
# дугові підписи, логотип по дузі (♏), DMS, ASC/MC/IC/DSC, хорди аспектів, таблиця аспектів

import os
import json
import math
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from matplotlib.patches import Wedge
import matplotlib.colors as mcolors
from flatlib import aspects as f_aspects
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from math import cos, sin, radians, pi

from matplotlib.lines import Line2D
import numpy as np

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz

import swisseph as swe
from flatlib.chart import Chart
from flatlib import const
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
CACHE_TTL_DAYS = 0.01

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
    "Ascendant":"ASC","MC":"MC",
    "Pars Fortuna":"⚶"
}
PLANET_SYMBOLS.update({
    "Chiron":"⚷", "Lilith":"⚸", "Ceres":"⚳", "Pallas":"⚴", "Juno":"⚵", "Vesta":"⚶"
})
PLANET_COLORS = {
    "Sun":"#f6c90e","Moon":"#c0c0c0","Mercury":"#7d7d7d","Venus":"#e88fb4","Mars":"#e55d5d",
    "Jupiter":"#f3a33c","Saturn":"#b78b68","Uranus":"#69d2e7","Neptune":"#6a9bd1","Pluto":"#3d3d3d",
    "Ascendant":"#2ecc71","MC":"#8e44ad"
}
PLANET_COLORS.update({
    "Chiron":"#ff66cc", "Lilith":"#993399", "Ceres":"#66ff66", "Pallas":"#6699ff",
    "Juno":"#ffcc33", "Vesta":"#ff9966"
})

PLANETS = [
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
    "Uranus","Neptune","Pluto","Chiron","Lilith","Ceres","Pallas",
    "Juno","Vesta","North Node","South Node"
]

ASPECTS_DEF = {
    "conjunction": {"angle": 0,   "orb": 8, "color": "#D62728"},  # червоний
    "sextile":     {"angle": 60,  "orb": 6, "color": "#1F77B4"},  # синій
    "square":      {"angle": 90,  "orb": 6, "color": "#FF7F0E"},  # оранжевий
    "trine":       {"angle": 120, "orb": 8, "color": "#2CA02C"},  # зелений
    "opposition":  {"angle": 180, "orb": 8, "color": "#9467BD"},  # фіолетовий
    "semisextile": {"angle": 30,  "orb": 2, "color": "#8C564B"},  # коричневий
    "semisquare":  {"angle": 45,  "orb": 3, "color": "#E377C2"},  # рожевий
    "quincunx":    {"angle": 150, "orb": 3, "color": "#7F7F7F"},  # сірий
    "quintile":    {"angle": 72,  "orb": 2, "color": "#17BECF"},  # бірюзовий
    "biquintile":  {"angle": 144, "orb": 2, "color": "#BCBD22"},  # оливковий
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
    if s == 60:
        s = 0; m += 1
    if m == 60:
        m = 0; d = (d + 1) % 360
    return f"{d}°{m}'{s}\""

def deg_to_dms_str(angle_float):
    return deg_to_dms(angle_float)

def zodiac_position(lon):
    """Повертає (знак, градус у знаку) для довготи"""
    lon = lon % 360.0
    sign_index = int(lon // 30)   # 0=Овен, 1=Телець, ..., 11=Риби
    deg_in_sign = lon % 30.0
    return sign_index, deg_in_sign

def to_theta_global_raw(degree):
    # legacy helper — не використовуєм без asc; надалі використовуємо локальний to_theta
    return np.deg2rad(90.0 - float(degree))

def geocode_place(place, retries=2, timeout=8):
    for attempt in range(retries + 1):
        try:
            loc = geolocator.geocode(place, timeout=timeout)
            if loc:
                return float(loc.latitude), float(loc.longitude)
            if "," not in place and attempt == 0:
                try_place = f"{place}, Ukraine"
                loc2 = geolocator.geocode(try_place, timeout=timeout)
                if loc2:
                    return float(loc2.latitude), float(loc2.longitude)
            return None, None
        except GeocoderTimedOut:
            continue
        except Exception:
            break
    return None, None

def get_house_lon(chart, i):
    # існуюча функція — повертає lon або None
    try:
        return chart.houses[i-1].lon
    except Exception:
        pass
    try:
        return chart.houses[i].lon
    except Exception:
        pass
    try:
        return chart.houses.get(i).lon
    except Exception:
        pass
    return None

def safe_house_lon(chart, i, asc_fallback=0.0):
    """
    Безпечне читання кута дому i. Якщо немає cusp у chart, повертає asc_fallback + (i-1)*30.
    Повертає float градуси (0..360).
    """
    try:
        v = get_house_lon(chart, i)
        if v is not None:
            return float(v) % 360.0
    except Exception:
        pass
    # спробуємо взяти ASC з chart, інакше використовуємо asc_fallback
    try:
        asc_obj = None
        try:
            asc_obj = chart.get("ASC")
        except Exception:
            asc_obj = None
        if asc_obj is not None:
            asc_val = getattr(asc_obj, "lon", None)
            if asc_val is not None:
                asc_fallback = float(asc_val) % 360.0
    except Exception:
        pass
    # поділ по 30 градусів від ASC
    return (float(asc_fallback) + (i - 1) * 30.0) % 360.0

ZODIAC_SIGNS = ["\u2648","\u2649","\u264A","\u264B","\u264C","\u264D",
                "\u264E","\u264F","\u2650","\u2651","\u2652","\u2653"]

def deg_in_sign_dms(lon_float):
    lon = float(lon_float) % 360.0
    sign_idx = int(lon // 30)
    within = lon % 30
    d = int(within)
    m_f = (within - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    if s == 60:
        s = 0; m += 1
    if m == 60:
        m = 0; d = (d + 1) % 30
    return f"{ZODIAC_SIGNS[sign_idx]} {d}°{m}'{s}\""

# ------------ координати/перетворення --------------
def pol2cart(theta, r):
    return r * np.cos(theta), r * np.sin(theta)

def cart2pol(x, y):
    theta = np.arctan2(y, x)
    r = np.hypot(x, y)
    return theta, r

def compute_aspects_manual(objects):
    results = []
    # беремо об'єкти, які мають lon і id (розширена фільтрація)
    objs = [o for o in objects if getattr(o, "id", None) and getattr(o, "lon", None) is not None]
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            p1, p2 = objs[i], objs[j]
            a1 = float(getattr(p1, "lon", 0.0)) % 360
            a2 = float(getattr(p2, "lon", 0.0)) % 360
            diff = abs(a1 - a2)
            if diff > 180:
                diff = 360 - diff
            for name, cfg in ASPECTS_DEF.items():
                if abs(diff - cfg["angle"]) <= cfg["orb"]:
                    results.append({
                        "planet1": getattr(p1, "id", str(p1)),
                        "planet1_symbol": PLANET_SYMBOLS.get(getattr(p1, "id", ""), ""),
                        "planet2": getattr(p2, "id", str(p2)),
                        "planet2_symbol": PLANET_SYMBOLS.get(getattr(p2, "id", ""), ""),
                        "type": name,
                        "angle": round(diff, 2),
                        "angle_dms": deg_to_dms(diff),
                        "color": cfg["color"]
                    })
                    break
    return results

# ----------------- Малювання карти -----------------
LOGO_TEXT = "NatalChart"

def draw_natal_chart(date, time, location, planets_list, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(10,10))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')

    # --- Крок 3: Сектори будинків ---
    house_colors = [
        "#FFCDD2","#F8BBD0","#E1BEE7","#D1C4E9","#C5CAE9","#BBDEFB",
        "#B3E5FC","#B2EBF2","#B2DFDB","#C8E6C9","#DCEDC8","#F0F4C3"
    ]
    house_angles = [(i*30, (i+1)*30) for i in range(12)]
    for i, (start, end) in enumerate(house_angles):
        wedge = Wedge((0,0), 1.0, start, end, facecolor=house_colors[i], alpha=0.3)
        ax.add_patch(wedge)
        angle_rad = math.radians((start+end)/2)
        x = 1.05*math.cos(angle_rad)
        y = 1.05*math.sin(angle_rad)
        ax.text(x, y, str(i+1), fontsize=12, fontweight='bold', ha='center', va='center')

    # --- Крок 4: Зодіак ---
    zodiac_symbols = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
    for i, sym in enumerate(zodiac_symbols):
        angle_rad = math.radians(i*30 + 15)
        x = 1.15*math.cos(angle_rad)
        y = 1.15*math.sin(angle_rad)
        ax.text(x, y, sym, fontsize=14, fontweight='bold', ha='center', va='center', color='darkblue')

    # --- Крок 2: ASC/MC/IC/DSC (приклад) ---
    asc_deg, mc_deg = 0, 90
    dsc_deg = (asc_deg+180)%360
    ic_deg = (mc_deg+180)%360
    angles = {'ASC': asc_deg, 'MC': mc_deg, 'DSC': dsc_deg, 'IC': ic_deg}
    for name, deg in angles.items():
        rad = math.radians(deg)
        x = 1.1*math.cos(rad)
        y = 1.1*math.sin(rad)
        ax.text(x, y, name, fontsize=10, fontweight='bold', color='gold')
        ax.plot([0, 0.95*math.cos(rad)], [0, 0.95*math.sin(rad)], color='gold', lw=1.5)

    # --- Крок 1: Планети ---
    planet_positions = []
    for p in planets_list:
        angle_rad = math.radians(p['angle'])
        x = 0.8*math.cos(angle_rad)
        y = 0.8*math.sin(angle_rad)
        ax.plot(x, y, 'o', markersize=10, label=p['name'])
        ax.text(x*1.1, y*1.1, p['symbol'], fontsize=12, ha='center', va='center')
        planet_positions.append({'name':p['name'], 'symbol':p['symbol'], 'angle':p['angle'], 'x':x, 'y':y})

    # --- Крок 5: Аспекти по Flatlib ---
    # Створюємо Chart (для реальних аспектів)
    chart_data = {p['name']: {'longitude': p['angle']} for p in planets_list}
    # Тобі можна тут підключити реальний Flatlib Chart, якщо є точна дата, час, місце
    # Поки будемо робити хорди між усіма планетами як приклад
    aspect_colors = {
        'conjunction': '#D62728', 'sextile': '#1F77B4', 'square': '#E377C2',
        'trine': '#2CA02C', 'opposition':'#9467BD', 'semisextile':'#8C564B',
        'semisquare':'#E377C2','quincunx':'#7F7F7F','biquintile':'#BCBD22'
    }
    aspects_table = []
    for i in range(len(planet_positions)):
        for j in range(i+1, len(planet_positions)):
            x1, y1 = planet_positions[i]['x'], planet_positions[i]['y']
            x2, y2 = planet_positions[j]['x'], planet_positions[j]['y']
            ax.plot([x1,x2],[y1,y2], color='gray', lw=0.8, alpha=0.5)
            angle_diff = abs(planet_positions[i]['angle'] - planet_positions[j]['angle'])
            if angle_diff>180: angle_diff = 360-angle_diff
            aspects_table.append({
                "planet1": planet_positions[i]['name'],
                "planet2": planet_positions[j]['name'],
                "angle": round(angle_diff,2),
                "type": "unknown",
                "color":"gray"
            })

    # --- Крок 6: Логотип ---
    ax.text(0, 0, LOGO_TEXT, fontsize=16, fontweight='bold', color='purple', ha='center', va='center')

    plt.savefig(filename, dpi=150)
    plt.close()

    result_json = {
        "chart_url": filename,
        "planets": planets_list,
        "houses":[{"number":i+1,"start":start,"end":end} for i,(start,end) in enumerate(house_angles)],
        "zodiac_symbols":zodiac_symbols,
        "asc_mc_dsc_ic":angles,
        "aspects_table":aspects_table
    }
    return result_json
# ----------------- /generate -----------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()
        data = request.get_json() or {}
        name = data.get("name") or data.get("firstName") or "Person"
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place") or data.get("city") or data.get("location")
        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date (YYYY-MM-DD), time (HH:MM) та place (рядок)"}), 400

        key = cache_key(name, date_str, time_str, place)
        json_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_path  = os.path.join(CACHE_DIR, f"{key}.png")

        # кеш
        if os.path.exists(json_path) and os.path.exists(png_path):
            try:
                mtime = dt.fromtimestamp(os.path.getmtime(json_path))
                if dt.now() - mtime <= timedelta(days=CACHE_TTL_DAYS):
                    with open(json_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    base_url = request.host_url.rstrip("/")
                    cached["chart_url"] = f"{base_url}/cache/{key}.png"
                    return jsonify(cached)
            except Exception:
                pass

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
            return jsonify({"error": "Exception", "message": str(e)}), 400

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

        # planets для JSON
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
                "angle": asp["angle"],
                "angle_dms": float_to_dms(asp["angle"]),
                "color": ASPECTS_DEF.get(asp["type"], {}).get("color", "#777777")
            })

        out = {
            "name": name, "date": date_str, "time": time_str,
            "place": place, "timezone": tz_str,
            "aspects_json": aspects_json,
            "aspects_table": aspects_table,
            "planets": planets_list,
            "chart_url": f"{request.host_url.rstrip('/')}/cache/{key}.png"
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return jsonify(out)

    except Exception as e:
        print("Unhandled error in /generate:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

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