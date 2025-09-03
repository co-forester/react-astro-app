# app.py — професійна натальна карта (Placidus), кеш PNG/JSON,
# дугові підписи, логотип по дузі (♏), DMS, ASC/MC/IC/DSC, хорди аспектів, таблиця аспектів

import os  # робота з файлами та директоріями
import json  # збереження/читання JSON
import hashlib  # генерація ключів для кешу
import traceback  # для відлову помилок
from datetime import datetime as dt, timedelta  # для роботи з датами

from matplotlib.patches import Wedge
import matplotlib.colors as mcolors


from flask import Flask, request, jsonify, send_from_directory  # веб-сервер, API
from flask_cors import CORS  # для доступу з фронтенду

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")  # без GUI
import matplotlib.pyplot as plt  # малювання карти
from matplotlib.lines import Line2D  # для легенди
import numpy as np  # для обчислень кутів

from geopy.geocoders import Nominatim  # геокодування
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder  # таймзона
import pytz  # робота з часовими зонами

import swisseph as swe  # Swiss Ephemeris — позиції планет
from flatlib.chart import Chart  # Flatlib — натальна карта
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos


# ----------------- Ініціалізація -----------------
# ================== Ініціалізація ефемерид ==================
EPHE_DIR = os.environ.get("EPHE_DIR", "/ephe")  # шлях до ефемерид
if not os.path.exists(EPHE_DIR):
    print(f"WARNING: Ефемериди не знайдені за шляхом {EPHE_DIR}")
swe.set_ephe_path(EPHE_DIR)  # встановлюємо локальний шлях для Swiss Ephemeris

# ================== Flask ==================
app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL_DAYS = 0.01

geolocator = Nominatim(user_agent="albireo_astro_app")
tf = TimezoneFinder() # таймзона

# ----------------- Конфіг -----------------
ZODIAC_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]  # символи зодіаку
ZODIAC_NAMES   = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                  "Стрілець","Козеріг","Водолій","Риби"]  # назви знаків

# Соковиті, насичені градієнти для будинків (start_color, end_color)
HOUSE_COLORS = [
    ("#f9b9b7", "#f28c8c"), ("#f48fb1", "#f06292"), ("#ce93d8", "#ab47bc"), ("#b39ddb", "#7e57c2"),
    ("#9fa8da", "#5c6bc0"), ("#90caf9", "#42a5f5"), ("#81d4fa", "#29b6f6"), ("#80deea", "#26c6da"),
    ("#80cbc4", "#26a69a"), ("#a5d6a7", "#66bb6a"), ("#c5e1a5", "#9ccc65"), ("#e6ee9c", "#d4e157")
]

# Планети, символи, кольори
PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "North Node":"☊","South Node":"☋","Ascendant":"ASC","MC":"MC",
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

# Аспекти (кут, орб, колір)
ASPECTS_DEF = {
    "conjunction": {"angle": 0,   "orb": 8, "color": "#D62728"},
    "sextile":     {"angle": 60,  "orb": 6, "color": "#1F77B4"},
    "square":      {"angle": 90,  "orb": 6, "color": "#FF7F0E"},
    "trine":       {"angle": 120, "orb": 8, "color": "#2CA02C"},
    "opposition":  {"angle": 180, "orb": 8, "color": "#9467BD"},
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

def to_theta(degree):
    """Перетворює астрологічні довготи у полярний кут для matplotlib"""
    return np.deg2rad(90 - degree)


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

ZODIAC_SIGNS = ["\u2648","\u2649","\u264A","\u264B","\u264C","\u264D",
                "\u264E","\u264F","\u2650","\u2651","\u2652","\u2653"]  # ♈..♓

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


# ----------------- Аспекти -----------------
def pol2cart(theta, r):
    # у системі matplotlib-поляр: x = r*cos(θ), y = r*sin(θ)
    return r * np.cos(theta), r * np.sin(theta)

def cart2pol(x, y):
    theta = np.arctan2(y, x)
    r = np.hypot(x, y)
    return theta, r

def compute_aspects_manual(objects):
    
    results = []
    objs = [o for o in objects if getattr(o, "id", None) in PLANET_SYMBOLS]
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            p1, p2 = objs[i], objs[j]
            a1 = getattr(p1, "lon", 0) % 360
            a2 = getattr(p2, "lon", 0) % 360
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
def draw_natal_chart(chart, aspects_list, save_path, name_for_center=None,
                     logo_text="Albireo Daria", logo_sign="Скорпіон"):
    try:
        # --- Фон + орієнтація ---
        fig = plt.figure(figsize=(12, 12))
        ax = plt.subplot(111, polar=True)

        # 1) ASC зліва: нульовий напрямок = захід (W), кути зростають за годинниковою
        ax.set_theta_zero_location("W")
        ax.set_theta_direction(-1)

        # 2) Радіальні межі колеса
        ax.set_ylim(0, 1.5)

        # 3) Чисте тло
        ax.set_xticks([]); ax.set_yticks([])
        fig.patch.set_facecolor("#4e4247")
        ax.set_facecolor("#4e4247")
        plt.rcParams["font.family"] = "DejaVu Sans"

        # 4) Жорстко фіксуємо пропорції (круг не спотворюється)
        ax.set_aspect('equal', 'box')

        # 5) Невелика внутрішня відступ-зсув, щоб нічого не «обрізало»
        ax.set_rorigin(-0.02)

        # --- Надійні утиліти всередині ---
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

        # ASC (fallback якщо треба)
        asc_obj = safe_get(chart, "ASC") or safe_get(chart, "Asc") or safe_get(chart, "asc")
        if asc_obj is None:
            try:
                asc_lon = float(getattr(chart.houses[0], "lon", 0.0)) % 360.0
                app.logger.warning("ASC not found; using houses[0].lon as fallback: %s", asc_lon)
            except Exception:
                asc_lon = 0.0
                app.logger.warning("ASC not found and houses[0] not available; using 0.0")
        else:
            try:
                asc_lon = float(getattr(asc_obj, "lon", 0.0)) % 360.0
            except Exception:
                asc_lon = 0.0

        def to_theta(lon):
            # переводимо довготу (0..360) у радіани з ротацією на ASC
            return np.deg2rad((float(lon) - asc_lon) % 360.0)

        # --- 1) Сектори будинків з градієнтом (малими смужками) ---
        house_sector_inner = 0.15
        house_sector_width = 0.25
        grad_steps = 24

        for i in range(1, 13):
            cusp1 = get_house_lon(chart, i)
            cusp2 = get_house_lon(chart, (i % 12) + 1)
            if cusp1 is None or cusp2 is None:
                continue

            start_deg = float(cusp1) % 360.0
            end_deg = float(cusp2) % 360.0
            span = (end_deg - start_deg) % 360.0
            if span <= 0:
                span += 360.0

            color_start, color_end = HOUSE_COLORS[(i - 1) % len(HOUSE_COLORS)]
            cmap = mcolors.LinearSegmentedColormap.from_list(f"house{i}_cmap", [color_start, color_end])

            # малюємо ряд тонких секцій для градієнта
            for step in range(grad_steps):
                frac1 = step / grad_steps
                frac2 = (step + 1) / grad_steps
                angle1 = start_deg + span * frac1
                angle2 = start_deg + span * frac2
                color = cmap(frac1)
                ax.bar(
                    x=to_theta(angle1),
                    height=house_sector_width,
                    width=np.deg2rad((angle2 - angle1) % 360.0),
                    bottom=house_sector_inner,
                    color=color,
                    alpha=0.55,
                    edgecolor=None,
                    align="edge",
                    zorder=1
                )

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

        # --- 6) ASC/MC/DSC/IC з маркерами та стрілками (safe_get використовується) ---
        r_marker = 1.38
        arrow_len = 0.07
        for label in ["ASC", "MC", "DSC", "IC"]:
            try:
                obj = safe_get(chart, label)
                if obj is None:
                    continue
                lon = float(getattr(obj, "lon", 0.0)) % 360.0
                th = to_theta(lon)
                ax.plot([th], [r_marker], marker='o', markersize=9, color="#FFD700", zorder=12)
                ax.annotate("", xy=(th, r_marker - arrow_len), xytext=(th, r_marker),
                            arrowprops=dict(facecolor="#FFD700", shrink=0.05, width=2, headwidth=8), zorder=12)
                label_text = f"{label} {deg_in_sign_dms(lon)}"
                ax.text(th, r_marker + 0.05, label_text, ha='center', va='center',
                        fontsize=10, color="#FFD700", fontweight="bold", zorder=12, rotation=0)
            except Exception:
                continue

        # --- 7) Планети (використовуємо to_theta для всіх) ---
        r_planet = 0.85
        planet_positions = {}
        # порядок планет/об'єктів, які хочемо показати
        planets_order = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto",
                         "Chiron","Lilith","Ceres","Pallas","Juno","Vesta","North Node","South Node"]
        chart_obj_map = {getattr(obj, "id", ""): obj for obj in chart.objects if getattr(obj, "id", None)}

        for pid in planets_order:
            sym = PLANET_SYMBOLS.get(pid, pid)
            obj = chart_obj_map.get(pid, None)
            if obj is None:
                continue
            lon = getattr(obj, "lon", None) or getattr(obj, "signlon", None)
            if lon is None:
                continue
            lon = float(lon) % 360.0
            th = to_theta(lon)
            col = PLANET_COLORS.get(pid, "#ffffff")
            ax.plot([th], [r_planet], marker='o', markersize=7, color=col, zorder=12)
            ax.text(th, r_planet + 0.05, sym, fontsize=18,
                    ha="center", va="center", color=col, zorder=11)
            ax.text(th, r_planet, deg_in_sign_dms(lon), fontsize=8,
                    ha="center", va="center", color=col, zorder=11)
            planet_positions[pid] = (th, r_planet, lon)

       # --- 8) Аспекти (хорди між planet_positions) ---
        for asp in aspects_list:
            try:
                p1_id = asp.get("planet1")
                p2_id = asp.get("planet2")
                if p1_id not in planet_positions or p2_id not in planet_positions:
                    continue

                th1, r1, _ = planet_positions[p1_id]
                th2, r2, _ = planet_positions[p2_id]
                cfg = ASPECTS_DEF.get(asp.get("type", "").lower(), {"color": "#777777", "orb": 5})
                col = cfg["color"]
                orb = cfg.get("orb", 5)
                diff = asp.get("angle", 0)
                width = max(1.5, 4 - abs(diff - cfg["angle"]) / orb)

                # трохи всередину, щоб лінія не перекривала символи планет
                r_used = min(r1, r2) * 0.82
                x1, y1 = pol2cart(th1, r_used)
                x2, y2 = pol2cart(th2, r_used)

                # малюємо хорду у XY
                ax.plot([x1, x2], [y1, y2],
                        color=col, lw=width, alpha=0.95, zorder=10,
                        transform=ax.transData._b)  # 👈 ключ: малюємо у декартових координатах
            except Exception:
                continue

        # --- 9) Легенда ---
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

        # --- Збереження (менше обрізання) ---
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