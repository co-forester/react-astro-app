# app.py — професійна натальна карта (Placidus), кеш PNG/JSON,
# дугові підписи, логотип по дузі (♏), DMS, ASC/MC/IC/DSC, хорди аспектів, таблиця аспектів
import os
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
import numpy as np

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# ----------------- Ініціалізація -----------------
app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)   # створює папку "cache", якщо її ще нема
CACHE_TTL_DAYS = 0.01                    # "Time To Live" — файли старше 30 днів треба видаляти

geolocator = Nominatim(user_agent="albireo_astro_app")
tf = TimezoneFinder()

# ----------------- Конфіг -----------------
ZODIAC_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
ZODIAC_NAMES   = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                  "Стрілець","Козеріг","Водолій","Риби"]

# Соковиті, насичені градієнти для будинків (start_color, end_color)
HOUSE_COLORS = [
    ("#f9b9b7", "#f28c8c"), ("#f48fb1", "#f06292"), ("#ce93d8", "#ab47bc"), ("#b39ddb", "#7e57c2"),
    ("#9fa8da", "#5c6bc0"), ("#90caf9", "#42a5f5"), ("#81d4fa", "#29b6f6"), ("#80deea", "#26c6da"),
    ("#80cbc4", "#26a69a"), ("#a5d6a7", "#66bb6a"), ("#c5e1a5", "#9ccc65"), ("#e6ee9c", "#d4e157")
]

# Планети, символи, кольори (світлі, контрастні)
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

# Аспекти (кут, орб, колір) — назви у нижньому регістрі
ASPECTS_DEF = {
    "conjunction": {"angle": 0,   "orb": 8, "color": "#D62728"},
    "sextile":     {"angle": 60,  "orb": 6, "color": "#1F77B4"},
    "square":      {"angle": 90,  "orb": 6, "color": "#FF7F0E"},
    "trine":       {"angle": 120, "orb": 8, "color": "#2CA02C"},
    "opposition":  {"angle": 180, "orb": 8, "color": "#9467BD"},
}

# ----------------- Утиліти -----------------
def cleanup_cache(days: int = CACHE_TTL_DAYS):
    now_ts = dt.now().timestamp()  # поточний час у секундах (UNIX timestamp)

    for fname in os.listdir(CACHE_DIR):  # перебирає всі файли у папці cache/
        fpath = os.path.join(CACHE_DIR, fname)
        try:
            if os.path.isfile(fpath):  # перевіряє, що це саме файл, а не папка
                # скільки часу пройшло від останньої модифікації файлу
                if now_ts - os.path.getmtime(fpath) > days * 24 * 3600:
                    os.remove(fpath)   # якщо файл старший за `days`, видаляє його
        except Exception:
            pass   # у випадку помилки просто ігнорує
        
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

def geocode_place(place, retries=2, timeout=8):
    """Повертає (lat, lon) або (None, None) — з retry на таймаут."""
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

# ----------------- Аспекти (ручний розрахунок) -----------------
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
                        "type": name,  # нижній регістр
                        "angle": round(diff, 2),
                        "angle_dms": deg_to_dms(diff),
                        "color": cfg["color"]
                    })
                    break
    return results

def draw_natal_chart(chart, aspects_list, save_path, name_for_center=None, logo_text="Albireo Daria"):
    try:
        # --- Створюємо фігуру та полярну вісь ---
        fig = plt.figure(figsize=(12, 12))               # Створюємо квадратну фігуру для карти
        ax = plt.subplot(111, polar=True)               # Полярна вісь для кругової карти
        ax.set_theta_zero_location("W")                 # 0° на заході (ліва частина кола)
        ax.set_theta_direction(-1)                      # Напрямок годинникової стрілки проти стандартного
        ax.set_ylim(0, 1.45)                            # Радіус від центру до зовнішніх елементів
        ax.set_xticks([]); ax.set_yticks([])            # Прибираємо стандартні позначки градусів
        fig.patch.set_facecolor("white")                # Фон фігури
        ax.set_facecolor("white")                        # Фон осі
        plt.rcParams["font.family"] = "DejaVu Sans"      # Шрифт для всієї карти

        # ----------------- 1) Сектори будинків (Placidus) -----------------
        try:
            for i in range(1, 13):                       # Проходимо по всіх 12 будинках
                cusp1 = get_house_lon(chart, i)          # Довгота початку дому i
                cusp2 = get_house_lon(chart, (i % 12) + 1)  # Довгота початку наступного дому
                if cusp1 is None or cusp2 is None:       # Якщо дані відсутні
                    raise RuntimeError("house cusps not available")  

                start_deg = cusp1 % 360                   # Коригуємо градуси у межах 0–360
                end_deg   = cusp2 % 360
                if (end_deg - start_deg) <= 0:           # Корекція для переходу через 0°
                    end_deg += 360

                theta_start = np.deg2rad(start_deg)      # Перетворення в радіани
                theta_end   = np.deg2rad(end_deg)
                width = abs(theta_end - theta_start)     # Ширина сектора

                ax.bar(
                    x=(theta_start + theta_end)/2,       # Середина сектора
                    height=1.08,                          # Радіус до зовнішнього краю
                    width=width,                          # Ширина дуги
                    bottom=0.0,                           # Початок від центру
                    color=HOUSE_COLORS[(i-1)%12][0],     # Основний колір дому
                    alpha=0.30,                           # Прозорість сектора
                    edgecolor=HOUSE_COLORS[(i-1)%12][1], # Кольорова обводка
                    linewidth=0.6,
                    zorder=0
                )

                # Лінії-секторні границі
                ax.plot([np.deg2rad(start_deg), np.deg2rad(start_deg)],
                        [0.15, 1.12], color="#888888", lw=0.8, zorder=2)

            # ----------------- Номери будинків -----------------
            house_number_radius = 0.16 + 0.03                 # Відступ від центру, щоб не перекривалися
            for i in range(1, 13):
                cusp1 = get_house_lon(chart, i)
                cusp2 = get_house_lon(chart, (i % 12) + 1)
                start = cusp1 % 360
                end   = cusp2 % 360
                diff  = (end - start) % 360
                mid   = (start + diff / 2.0) % 360
                th_mid = np.deg2rad(mid)
                ax.text(
                    th_mid, house_number_radius, str(i),
                    fontsize=9, ha="center", va="center",
                    color="#6a1b2c", fontweight="bold", zorder=7
                )
        except Exception:                                   # fallback на рівні 30°/30°
            house_number_radius = 0.16 + 0.03
            for i in range(12):
                th_start = np.deg2rad(i*30)
                th_end   = np.deg2rad(i*30 + 30)
                width = th_end - th_start
                ax.bar(
                    x=(th_start + th_end)/2, height=1.08, width=width, bottom=0.0,
                    color=HOUSE_COLORS[i % 12][0], alpha=0.26,
                    edgecolor=HOUSE_COLORS[i % 12][1], linewidth=0.6, zorder=0
                )
                ax.plot([th_start, th_start], [0.15, 1.12], color="#888888", lw=0.8, zorder=2)
                th_mid = np.deg2rad(i*30 + 15)
                ax.text(
                    th_mid, house_number_radius, str(i+1),
                    fontsize=9, ha="center", va="center",
                    color="#6a1b2c", fontweight="bold", zorder=7
                )

        # ----------------- 2) Бордове кільце Зодіаку + символи та назви по дузі -----------------
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i * 30
            theta_start = np.deg2rad(start)
            theta_end = np.deg2rad(start + 30)
            width = abs(theta_end - theta_start)

            # Широке бордове кільце
            ax.bar(x=(theta_start + theta_end) / 2, height=0.20, width=width, bottom=1.10,
                   color="#6a1b2c", edgecolor="white", linewidth=1.2, zorder=3)
            ax.plot([theta_start, theta_start], [1.10, 1.30], color="white", lw=1.2, zorder=4)

            center_deg = start + 15
            theta_c = np.deg2rad(center_deg)
            text_rot = -center_deg
            if sym == "♏":
                # Скорпіон: залишаємо місце для логотипу, тільки символ
                ax.text(theta_c, 1.18, sym, fontsize=20, ha="center", va="center",
                        color="#FFD700", fontweight="bold", rotation=text_rot,
                        rotation_mode="anchor", zorder=6)
            else:
                ax.text(theta_c, 1.18, sym, fontsize=20, ha="center", va="center",
                        color="white", fontweight="bold", rotation=text_rot,
                        rotation_mode="anchor", zorder=5)
                ax.text(theta_c, 1.27, ZODIAC_NAMES[i], fontsize=9, ha="center", va="center",
                        color="white", rotation=text_rot,
                        rotation_mode="anchor", zorder=5)

            # Дугові внутрішні риски 5°
            for deg_mark in range(0, 31, 5):
                theta_deg = np.deg2rad(start + deg_mark)
                r_start = 1.09
                r_end = 1.10 if deg_mark % 10 == 0 else 1.095
                ax.plot([theta_deg, theta_deg], [r_start, r_end], color="#faf6f7", lw=1, zorder=2)

        # ----------------- 3) Градуйовка 10°/30° -----------------
        for deg in range(0, 360, 10):
            th = np.deg2rad(deg)
            r0 = 1.08
            r1 = 1.10 if deg % 30 == 0 else 1.095
            lw = 1.0 if deg % 30 == 0 else 0.6
            col = "#333333" if deg % 30 == 0 else "#777777"
            ax.plot([th, th], [r0, r1], color=col, lw=lw, zorder=4)
            if deg % 30 == 0:
                ax.text(th, 1.305, f"{deg}°", fontsize=8, ha="center", va="center", color="#aaaaaa")
                ax.text(th, 1.325, deg_to_dms(deg), fontsize=7, ha="center", va="center", color="#888888")

        # ----------------- 4) Центральне коло (світлий бордовий) та ім'я всередині -----------------
        central_circle_radius = 0.16                   # Радіус центрального кола
        ax.set_aspect("equal")                         # Квадратне співвідношення осей, щоб коло не іскривилось
        central_circle = plt.Circle(
            (0, 0), central_circle_radius,
            color="#e9c7cf", fill=True,                # Світлий бордовий фон
            ec="#a05c6a", lw=1.1,                      # Обводка кола
            alpha=0.97, zorder=12                       # Порядок відображення
        )
        ax.add_artist(central_circle)                  # Додаємо коло на осі

        # Ім'я всередині кола, динамічний шрифт
        if name_for_center:
            base_fontsize = 13
            name_len = len(str(name_for_center))
            fontsize = max(8, int(base_fontsize * 13 / name_len)) if name_len > 13 else base_fontsize
            ax.text(
                0, 0, name_for_center, color="#800000", ha="center", va="center",
                fontsize=fontsize, fontweight="bold", zorder=13, clip_on=True
            )

        # ----------------- 5) Номери домів (по Placidus або fallback) -----------------
        house_number_radius = central_circle_radius + 0.03
        try:
            for i in range(1, 13):
                cusp1 = get_house_lon(chart, i)
                cusp2 = get_house_lon(chart, (i % 12) + 1)
                if cusp1 is None or cusp2 is None: raise RuntimeError
                start = cusp1 % 360
                end   = cusp2 % 360
                diff = (end - start) % 360
                mid = (start + diff / 2.0) % 360
                th_mid = np.deg2rad(mid)
                ax.text(th_mid, house_number_radius, str(i),
                        fontsize=9, ha="center", va="center", color="#6a1b2c", fontweight="bold", zorder=7)
        except Exception:
            for i in range(12):
                th_mid = np.deg2rad(i*30 + 15)
                ax.text(th_mid, house_number_radius, str(i+1),
                        fontsize=9, ha="center", va="center", color="#6a1b2c", fontweight="bold", zorder=7)

        # Далі йдуть ASC/MC/DSC/IC, планети, хорди аспектів, таблиця та логотип
        # ... (рядки залишені без змін, як у твоєму коді)
        # --- 6) ASC/MC/DSC/IC маркери та DMS ---
        r_marker = 1.34
        for label in ["ASC", "MC", "DSC", "IC"]:
            try:
                try:
                    obj = chart.get(label)
                except Exception:
                    try:
                        obj = chart.getObject(label)
                    except Exception:
                        obj = None
                if obj is None:
                    continue
                lon = getattr(obj, "lon", None)
                if lon is None:
                    continue
                th = np.deg2rad(float(lon) % 360)
                ax.plot([th], [r_marker - 0.02], marker='o', markersize=6, color="#FFD700", zorder=9)
                deg_i = int(float(lon))
                min_i = int((float(lon) - deg_i) * 60)
                sec_i = int(((float(lon) - deg_i) * 60 - min_i) * 60)
                label_text = f"{label} {deg_i}°{min_i}'{sec_i}''"
                ax.text(th, r_marker + 0.015, label_text, ha='center', va='center',
                        fontsize=8, color="#444444", zorder=9, rotation=0)
            except Exception:
                continue

        # --- 7) Планети: символи + DMS ---
        r_planet = 0.80
        planet_positions = {}
        for obj in chart.objects:
            try:
                oid = getattr(obj, "id", None)
                if oid in PLANET_SYMBOLS:
                    lon = getattr(obj, "lon", None)
                    if lon is None:
                        lon = getattr(obj, "signlon", None)
                    if lon is None:
                        continue
                    lon = float(lon) % 360
                    th = np.deg2rad(lon)
                    sym = PLANET_SYMBOLS[oid]
                    col = PLANET_COLORS.get(oid, "#333333")
                    ax.plot(th, r_planet, marker='o', markersize=6, color=col, zorder=12)
                    ax.text(th, r_planet + 0.07, sym, fontsize=20, ha="center", va="center", color=col, zorder=11)
                    ax.text(th, r_planet, f"{oid} {deg_to_dms(lon)}", fontsize=8,
                            ha="center", va="center", color=col, zorder=11)
                    planet_positions[oid] = (th, r_planet, lon)
            except Exception:
                continue

        # --- 8) Аспекти: хорди + таблиця ---
        aspect_colors = { "conjunction": "#D62728", "sextile": "#1F77B4", "square": "#FF7F0E",
                          "trine": "#2CA02C", "opposition": "#9467BD" }
        aspects_table = []
        legend_seen = {}
        for asp in aspects_list:
            try:
                p1_id = asp.get("planet1")
                p2_id = asp.get("planet2")
                if p1_id not in planet_positions or p2_id not in planet_positions:
                    continue
                th1, r1, lon1_f = planet_positions[p1_id]
                th2, r2, lon2_f = planet_positions[p2_id]
                col = aspect_colors.get(str(asp.get("type", "")).lower(), "#777777")
                ax.plot([th1, th2], [r1, r2], color=col, lw=2.2, alpha=0.95, zorder=10)

                def dms_str(x):
                    d = int(x) % 360
                    m = int((x - int(x)) * 60)
                    s = int(((x - int(x)) * 60 - m) * 60)
                    return f"{d}°{m}'{s}''"

                aspects_table.append({
                    "planet1": p1_id,
                    "lon1": dms_str(lon1_f),
                    "planet2": p2_id,
                    "lon2": dms_str(lon2_f),
                    "type": asp.get("type"),
                    "angle": asp.get("angle"),
                    "angle_dms": asp.get("angle_dms"),
                    "color": col
                })
                legend_seen[str(asp.get("type","")).lower()] = col
            except Exception:
                continue

        # --- 9) Легенда ---
        legend_order = ["conjunction", "sextile", "square", "trine", "opposition"]
        legend_handles = []
        legend_labels = []
        for nm in legend_order:
            if nm in legend_seen:
                col = legend_seen[nm]
                legend_handles.append(Line2D([0], [0], color=col, lw=4))
                legend_labels.append(nm.title())
        if legend_handles:
            ax_leg = fig.add_axes([0.05, -0.09, 0.90, 0.06])
            ax_leg.axis("off")
            ax_leg.legend(handles=legend_handles, labels=legend_labels,
                          loc="center", ncol=len(legend_handles), frameon=False)

        # --- 10) Таблиця аспектів під картою ---
        if aspects_table:
            cols = ["planet1", "lon1", "planet2", "lon2", "type", "angle_dms"]
            table_data = [[str(row.get(c, "")) for c in cols] for row in aspects_table]
            colors = [row.get("color", "#ffffff") for row in aspects_table]
            ax_tbl = fig.add_axes([0.03, -0.28, 0.94, 0.16])
            ax_tbl.axis("off")
            tbl = ax_tbl.table(cellText=table_data,
                               colLabels=["Planet 1","Lon 1","Planet 2","Lon 2","Aspect","Angle"],
                               loc="center", cellLoc="center")
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7)
            tbl.scale(1.0, 1.18)
            for r in range(1, len(table_data) + 1):
                for c in range(len(cols)):
                    cell = tbl[(r, c)]
                    cell.set_facecolor(matplotlib.colors.to_rgba(colors[r-1], 0.12))

        # --- 11) Логотип у секторі Скорпіона ---
        try:
            arc_start = np.deg2rad(236)
            arc_end   = np.deg2rad(214)
            r_logo = 1.27
            label = (logo_text or "Albireo Daria")
            thetas = np.linspace(arc_start, arc_end, len(label))
            for ch, th in zip(label, thetas):
                rotation_deg = -np.degrees(th) + 90 + 180
                ax.text(th, r_logo, ch, fontsize=9, ha='center', va='center',
                        color="#FFD700", rotation=rotation_deg, rotation_mode="anchor", zorder=8)
        except Exception:
            pass

        # Акцент на Асцендент (золотий маркер на рівні планет)
        try:
            asc_obj = chart.get(const.ASC)
            if asc_obj is not None:
                asc_lon = getattr(asc_obj, "lon", None)
                if asc_lon is not None:
                    th = np.deg2rad(float(asc_lon) % 360)
                    ax.plot([th], [r_planet], marker='o', markersize=9, color="#FFD700", zorder=12)
        except Exception:
            pass

        # >>> виправлення пропорцій
        ax.set_aspect("equal", adjustable="box")  

        # Збереження картинки
        try:
            plt.savefig(save_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
        finally:
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
        # Підтримка альтернативних ключів (city -> place)
        name = data.get("name") or data.get("firstName") or "Person"
        date_str = data.get("date")          # YYYY-MM-DD
        time_str = data.get("time")          # HH:MM
        place = data.get("place") or data.get("city") or data.get("location")

        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date (YYYY-MM-DD), time (HH:MM) та place (рядок)"}), 400

        key = cache_key(name, date_str, time_str, place)
        json_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_path  = os.path.join(CACHE_DIR, f"{key}.png")

        # Кеш-хіт
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

        # Геокодування
        lat, lon = geocode_place(place)
        if lat is None:
            return jsonify({"error": "Місце не знайдено (геокодер)"}), 400

        # Таймзона
        try:
            tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            tz = pytz.timezone(tz_str)
        except Exception:
            tz_str = "UTC"
            tz = pytz.timezone("UTC")

        # Local datetime -> flatlib Datetime (offset у годинах)
        try:
            naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            local_dt = tz.localize(naive)
            offset_hours = (local_dt.utcoffset().total_seconds() / 3600.0) if local_dt.utcoffset() else 0.0
        except Exception as e:
            return jsonify({"error": f"Невірний формат date/time: {str(e)}"}), 400

        # flatlib Datetime: 'YYYY/MM/DD' та 'HH:MM' і offset_hours
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)

        # Placidus (hsys='P'), fallback — як є
        try:
            chart = Chart(fdate, pos, hsys='P')  # 2 позиційних + ключовий параметр — ок
        except Exception:
            chart = Chart(fdate, pos)

        # Аспекти
        aspects_json = compute_aspects_manual(chart.objects)

        # Малювання PNG (і створення кеш-файла)
        try:
            draw_natal_chart(chart, aspects_json, png_path, name_for_center=name, logo_text="Albireo Daria")
        except Exception as e:
            base_url = request.host_url.rstrip("/")
            out = {
                "name": name, "date": date_str, "time": time_str,
                "place": place, "timezone": tz_str,
                "aspects_json": aspects_json,
                "aspects_table": aspects_json,  # дубль для зручності
                "chart_url": None,
                "warning": f"Помилка при малюванні картинки: {str(e)}"
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            return jsonify(out), 200

        # JSON-відповідь + кеш JSON
        base_url = request.host_url.rstrip("/")
        aspects_table = []
        for asp in aspects_json:
            aspects_table.append({
                "planet1": asp["planet1"],
                "planet2": asp["planet2"],
                "type": asp["type"],
                "angle": asp["angle"],
                "angle_dms": asp["angle_dms"],
                "color": ASPECTS_DEF.get(asp["type"], {}).get("color", "#777777")
            })

        out = {
            "name": name, "date": date_str, "time": time_str,
            "place": place, "timezone": tz_str,
            "aspects_json": aspects_json,
            "aspects_table": aspects_table,
            "chart_url": f"{base_url}/cache/{key}.png"
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
    # debug=True можна вимкнути на проді
    app.run(host="0.0.0.0", port=port, debug=True)