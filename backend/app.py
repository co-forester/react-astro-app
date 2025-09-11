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
def draw_natal_chart(chart, aspects_list, save_path, name_for_center=None,
                     logo_text="Albireo Daria", logo_sign="Скорпіон"):
    """
    Малює повну натальну карту:
      - ASC/MC/IC/DSC маркери + градуси,
      - сектори домів (градієнт) + номери домів,
      - кільце зодіаку з символами та градусними мітками,
      - планети (тільки ті, що є в chart.objects, які містять id),
      - хорди аспектів (з списку aspects_list),
      - легенда і центральний логотип/текст.
    """
    try:
        fig = plt.figure(figsize=(12, 12))
        ax = plt.subplot(111, polar=True)
        ax.set_theta_zero_location("W")
        ax.set_theta_direction(1)
        ax.set_ylim(0, 1.7)
        ax.set_xticks([]); ax.set_yticks([])
        fig.patch.set_facecolor("#4e4247")
        ax.set_facecolor("#4e4247")
        plt.rcParams["font.family"] = "DejaVu Sans"
        ax.set_aspect('equal', 'box')
        ax.set_rorigin(-0.02)

        # ---- допоміжні функції ----
        def safe_get(obj_chart, key):
            variants = []
            if isinstance(key, str):
                variants.extend([key, key.upper(), key.capitalize()])
            try:
                const_val = getattr(const, key.upper())
                if const_val:
                    variants.append(const_val)
            except Exception:
                pass
            for k in variants:
                try:
                    if k is None:
                        continue
                    res = obj_chart.get(k)
                    if res is not None:
                        return res
                except Exception:
                    continue
            return None

        # ASC (fallback на будинок 1 або 0.0)
        asc_obj = safe_get(chart, "ASC")
        asc_lon = None
        try:
            if asc_obj is not None and getattr(asc_obj, "lon", None) is not None:
                asc_lon = float(getattr(asc_obj, "lon"))
        except Exception:
            asc_lon = None
        if asc_lon is None:
            cusp1 = get_house_lon(chart, 1)
            if cusp1 is not None:
                asc_lon = float(cusp1)
        if asc_lon is None:
            asc_lon = 0.0

        # to_theta: приймає глобальний градус та повертає радіани відносно ASC
        def to_theta(lon):
            ang = (float(lon) - float(asc_lon)) % 360.0
            return np.deg2rad(ang)

        def to_theta_global(deg):
            return to_theta(deg)

        # DMS / degree helper
        def deg_in_sign_str(lon):
            lon = float(lon) % 360.0
            sign_idx = int(lon // 30)
            deg = int(lon % 30)
            return f"{deg}° {ZODIAC_SYMBOLS[sign_idx]}"

        # --- 1) Сектори домів (градієнт) ---
        house_sector_inner = 0.15
        house_sector_width = 0.25
        grad_steps = 18

        for i in range(1, 13):
            c1 = safe_house_lon(chart, i, asc_fallback=asc_lon)
            c2 = safe_house_lon(chart, (i % 12) + 1, asc_fallback=asc_lon)
            if c1 is None or c2 is None:
                continue
            start_deg = float(c1) % 360.0
            end_deg = float(c2) % 360.0
            span = (end_deg - start_deg) % 360.0
            if span <= 0:
                span += 360.0
            color_start, color_end = HOUSE_COLORS[(i - 1) % len(HOUSE_COLORS)]
            cmap = mcolors.LinearSegmentedColormap.from_list(f"house{i}_cmap", [color_start, color_end])

            # дрібні смуги для градієнта
            for step in range(grad_steps):
                frac1 = step / grad_steps
                frac2 = (step + 1) / grad_steps
                a1 = start_deg + span * frac1
                a2 = start_deg + span * frac2
                width = np.deg2rad((a2 - a1) % 360.0)
                ax.bar(
                    x=to_theta(a1),
                    height=house_sector_width,
                    width=width,
                    bottom=house_sector_inner,
                    color=cmap(frac1),
                    alpha=0.55,
                    edgecolor=None,
                    align="edge",
                    zorder=1
                )

        # --- 2) Радіальні межі домів ---
        r_inner = 0.15
        r_outer = 1.05
        for i in range(1, 13):
            cusp = safe_house_lon(chart, i, asc_fallback=asc_lon)
            if cusp is None:
                continue
            th = to_theta(cusp)
            ax.plot([th, th], [r_inner, r_outer], color="#888888", lw=0.9, zorder=2)

        # --- 3) Номери домів (біля центру) ---
        house_number_radius = 0.19
        for i in range(1, 13):
            c1 = safe_house_lon(chart, i, asc_fallback=asc_lon)
            c2 = safe_house_lon(chart, (i % 12) + 1, asc_fallback=asc_lon)
            if c1 is None or c2 is None:
                continue
            start = float(c1) % 360.0
            end = float(c2) % 360.0
            span = (end - start) % 360.0
            mid = (start + span / 2.0) % 360.0
            ax.text(to_theta(mid), house_number_radius, str(i),
                    fontsize=10, ha="center", va="center",
                    color="#ffffff", fontweight="bold", zorder=7)

        # --- 4) Кільце зодіаку (символи та мітки) ---
        ring_radius_start = 1.10
        ring_height = 0.18
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i * 30.0
            end = start + 30.0
            span = 30.0
            mid = (start + span / 2.0) % 360.0
            center = to_theta_global(mid)
            width = np.deg2rad(span)

            ax.bar(
                x=center,
                height=ring_height,
                width=width,
                bottom=ring_radius_start,
                color=HOUSE_COLORS[i % 12][0],
                edgecolor=HOUSE_COLORS[i % 12][1],
                linewidth=1.0,
                zorder=3,
                align='center'
            )

            # межі знаків
            ax.plot([to_theta_global(start), to_theta_global(start)],
                    [ring_radius_start, ring_radius_start + ring_height + 0.01],
                    color="white", lw=1.0, zorder=4)

            # символ та підпис знаку
            symbol_r = ring_radius_start + ring_height - 0.02
            label_r = ring_radius_start + 0.05
            ax.text(center, symbol_r, sym, fontsize=18, ha="center", va="center",
                    color="#ffffff", fontweight="bold", rotation=(mid + 90) % 360,
                    rotation_mode="anchor", zorder=6)
            ax.text(center, label_r, ZODIAC_NAMES[i], fontsize=9, ha="center", va="center",
                    color="#ffffff", rotation=(mid + 90) % 360, rotation_mode="anchor", zorder=5)

            # мітки 0-30° кожні 5°
            for deg_mark in range(0, 31, 5):
                theta_deg = to_theta_global(start + deg_mark)
                r_start = ring_radius_start + 0.01
                r_end = ring_radius_start + (0.02 if deg_mark % 10 == 0 else 0.015)
                ax.plot([theta_deg, theta_deg], [r_start, r_end], color="#faf6f7", lw=1, zorder=2)
                if deg_mark in [10, 20]:
                    r_text = ring_radius_start + ring_height + 0.03
                    ax.text(theta_deg, r_text, str(deg_mark), color='white', fontsize=8,
                            ha='center', va='center', zorder=5)

        # --- 5) ASC/MC/DSC/IC маркери + підписи (поза колом) ---
        r_marker = 1.62
        arrow_len = 0.07
        try:
            asc = float(getattr(chart.get("ASC"), "lon", asc_lon)) % 360
        except Exception:
            asc = float(asc_lon) % 360
        try:
            mc = float(getattr(chart.get("MC"), "lon", 0)) % 360
        except Exception:
            mc = 0.0
        dsc = (asc + 180.0) % 360
        ic = (mc + 180.0) % 360

        axes_points = {
            "ASC": (asc, "#00FF00"),
            "DSC": (dsc, "#FF0000"),
            "MC":  (mc, "#1E90FF"),
            "IC":  (ic, "#9400D3")
        }

        for label, (lon, col) in axes_points.items():
            th = to_theta(lon)
            ax.plot([th], [r_marker], marker="o", markersize=9, color=col, zorder=12)
            ax.annotate("", xy=(th, r_marker - arrow_len), xytext=(th, r_marker),
                        arrowprops=dict(facecolor=col, shrink=0.05, width=2, headwidth=8),
                        zorder=12)
            deg_in_sign = int(lon % 30)
            sign_idx = int(lon // 30)
            sign_symbol = ZODIAC_SYMBOLS[sign_idx]
            label_text = f"{label} {deg_in_sign}° {sign_symbol}"
            ax.text(th, r_marker + 0.05, label_text, ha="center", va="center",
                    fontsize=10, color=col, fontweight="bold", zorder=12)

        # --- 6) Планети (тільки основні, що в chart.objects) ---
        r_planet = 0.85
        planet_positions = {}
        chart_obj_map = {getattr(obj, "id", ""): obj for obj in chart.objects if getattr(obj, "id", None)}

        def get_lon(obj_id):
            obj = chart_obj_map.get(obj_id)
            if obj is None:
                return None
            return float(getattr(obj, "lon", getattr(obj, "signlon", 0.0))) % 360.0

        def deg_in_sign_label(lon):
            sign = int(lon // 30)
            deg = int(lon % 30)
            return f"{deg}° {ZODIAC_SYMBOLS[sign]}"

        # малюємо планети лише для тих id, які є в chart.objects
        for obj in chart.objects:
            pid = getattr(obj, "id", None)
            if pid is None:
                continue
            if pid not in PLANET_SYMBOLS and pid not in PLANETS:
                continue
            lon = get_lon(pid)
            if lon is None:
                continue
            th = to_theta(lon)
            col = PLANET_COLORS.get(pid, "#ffffff")
            ax.plot([th], [r_planet], marker='o', markersize=7, color=col, zorder=12)
            sym = PLANET_SYMBOLS.get(pid, pid)
            ax.text(th, r_planet + 0.05, sym, fontsize=16, ha="center", va="center", color=col, zorder=11)
            theta_deg = np.rad2deg(th)
            rotation = (theta_deg + 90) % 360
            ax.text(th, r_planet - 0.03, deg_in_sign_label(lon), fontsize=8, ha="center", va="center",
                    color=col, rotation=rotation, rotation_mode="anchor", zorder=11)

            planet_positions[pid] = (th, r_planet, lon)

        # --- 7) Аспекти як хорди (взяти з aspects_list) ---
        for asp in aspects_list or []:
            p1 = asp.get("planet1")
            p2 = asp.get("planet2")
            if not p1 or not p2:
                continue
            pos1 = planet_positions.get(p1)
            pos2 = planet_positions.get(p2)
            if not pos1 or not pos2:
                # можливо один з об'єктів не в planet_positions (напр. Syzygy) — пропускаємо
                continue
            color = asp.get("color") or ASPECTS_DEF.get(asp.get("type"), {}).get("color", "#999999")
            th1, r1 = pos1[0], pos1[1]
            th2, r2 = pos2[0], pos2[1]
            ax.plot([th1, th2], [r1, r2], color=color, linewidth=1.5, alpha=0.9, zorder=5)

        # --- 8) Центральний текст / логотип ---
        center_text = name_for_center or logo_text or "Albireo"
        ax.text(0, 0, center_text, fontsize=20, ha="center", va="center",
                color="#ffaa33", zorder=20, fontweight="bold")

        # --- 9) Легенда (планети + аспекти) ---
        legend_elements = []
        for pid, sym in PLANET_SYMBOLS.items():
            if pid in PLANET_COLORS:
                legend_elements.append(Line2D([0], [0], marker='o', color='w',
                                              markerfacecolor=PLANET_COLORS[pid],
                                              label=f"{sym} {pid}", markersize=8))
        for asp_name, cfg in ASPECTS_DEF.items():
            legend_elements.append(Line2D([0], [0], color=cfg["color"], lw=2.5, label=asp_name.capitalize()))
        ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.16),
                  fontsize=10, ncol=3, frameon=False)

        # save
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        plt.savefig(save_path, dpi=180, facecolor=fig.get_facecolor(), pad_inches=0.5)
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