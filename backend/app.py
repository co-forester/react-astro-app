import os
import math
import json
import hashlib
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

# -------------------- Flask --------------------
app = Flask(__name__)
CORS(app)

# -------------------- Globals --------------------
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

# Автоочистка кешу старше 30 днів
def cleanup_cache():
    now = dt.now()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.isfile(fpath):
            mtime = dt.fromtimestamp(os.path.getmtime(fpath))
            if now - mtime > timedelta(days=30):
                try:
                    os.remove(fpath)
                except:
                    pass

# Символи планет/точок
PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆",
    "Pluto": "♇", "North Node": "☊", "South Node": "☋",
    "Ascendant": "ASC", "MC": "MC", "Pars Fortuna": "⚶", "Syzygy": "Syzygy"
}

# Кольори планет (легкі, читабельні)
PLANET_COLORS = {
    "Sun": "gold", "Moon": "silver", "Mercury": "darkorange", "Venus": "deeppink",
    "Mars": "red", "Jupiter": "royalblue", "Saturn": "brown",
    "Uranus": "deepskyblue", "Neptune": "mediumslateblue", "Pluto": "purple",
    "Ascendant": "green", "MC": "black", "North Node": "dimgray", "South Node": "dimgray",
    "Pars Fortuna": "teal", "Syzygy": "gray"
}

# Аспекти: (кут, колір, орб)
ASPECTS = {
    "conjunction": (0,    "#cccccc", 8),
    "sextile":     (60,   "#f7eaea", 4),
    "square":      (90,   "#8b8b8b", 6),
    "trine":       (120,  "#d4a5a5", 6),
    "opposition":  (180,  "#4a0f1f", 8),
}

ZODIAC_SIGNS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]

# -------------------- Helpers --------------------
def md5_key(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def deg_to_rad(deg: float) -> float:
    return math.radians(deg % 360.0)

def angle_diff(a: float, b: float) -> float:
    """Мінімальна різниця кутів (0..180)."""
    d = abs((a - b) % 360.0)
    return d if d <= 180 else 360 - d

# Обчислення аспектів (ручна перевірка орбів)
def compute_aspects(chart):
    objs = [o for o in chart.objects if o.id in PLANET_SYMBOLS]
    results = []
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            p1, p2 = objs[i], objs[j]
            ang = angle_diff(p1.lon, p2.lon)
            for name, (target, color, orb) in ASPECTS.items():
                if abs(ang - target) <= orb:
                    results.append({
                        "planet1": p1.id,
                        "planet1_symbol": PLANET_SYMBOLS.get(p1.id, p1.id),
                        "planet2": p2.id,
                        "planet2_symbol": PLANET_SYMBOLS.get(p2.id, p2.id),
                        "type": name,
                        "angle": round(ang, 2),
                        "color": color
                    })
                    break
    return results

# -------------------- Drawing --------------------
def draw_chart(chart, filepath):
    # Полярна проєкція: 0° вгору, оберт за год.стрілкою
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})
    ax.set_facecolor("white")
    ax.set_theta_direction(-1)
    ax.set_theta_offset(math.pi / 2)
    ax.set_xticks([])
    ax.set_yticks([])

    # Радіальні рівні (щоб не було "овалу")
    inner_r = 0.50  # межа внутрішнього диска
    ring_r  = 1.00  # зовнішній радіус карти (планети ~0.90)

    # --- Фон секторів будинків (Placidus), пастельні напівпрозорі ---
    # Використаємо 12 кольорів з Pastel1
    for i, house in enumerate(chart.houses):
        start_deg = chart.houses[i].cusp
        end_deg   = chart.houses[(i + 1) % 12].cusp
        width_deg = (end_deg - start_deg) % 360.0
        start = deg_to_rad(start_deg)
        width = math.radians(width_deg) if width_deg != 0 else 2*math.pi
        ax.bar(
            x=start, height=(ring_r - inner_r), width=width,
            bottom=inner_r, align="edge",
            color=plt.cm.Pastel1(i / 12), alpha=0.35, edgecolor="none", zorder=0
        )

    # --- Кільце знаків зодіаку (по 30°) + підпис знаків ---
    for i in range(12):
        # межі знаку
        sign_start_deg = i * 30.0
        sign_mid_deg   = sign_start_deg + 15.0
        # тонка розмітка меж знаків
        ax.plot([deg_to_rad(sign_start_deg), deg_to_rad(sign_start_deg)], [inner_r, ring_r],
                lw=1.2, alpha=0.5, color="#aaaaaa", zorder=2)
        # підпис знаку зовні кільця
        ax.text(deg_to_rad(sign_mid_deg), ring_r + 0.03, ZODIAC_SIGNS[i],
                ha="center", va="center", fontsize=18, color="#222222", zorder=3)

    # --- Градуювання (кожні 10° короткі штрихи) ---
    for d in range(0, 360, 10):
        r0 = ring_r - 0.02
        r1 = ring_r
        lw = 0.8
        if d % 30 == 0:
            r0 = ring_r - 0.035
            lw = 1.2
        ax.plot([deg_to_rad(d), deg_to_rad(d)], [r0, r1], color="#999999", lw=lw, zorder=2, alpha=0.8)

    # --- Вісь ASC та MC (анотації) ---
    try:
        asc_obj = chart.get(const.ASC)
        mc_obj  = chart.get(const.MC)
        asc_ang = deg_to_rad(asc_obj.lon)
        mc_ang  = deg_to_rad(mc_obj.lon)

        ax.plot([asc_ang, asc_ang], [inner_r - 0.05, ring_r], color="green", lw=1.6, zorder=3)
        ax.text(asc_ang, inner_r - 0.07, "ASC", ha="center", va="center",
                fontsize=12, color="green", fontweight="bold", zorder=4)

        ax.plot([mc_ang, mc_ang], [inner_r - 0.05, ring_r], color="purple", lw=1.6, zorder=3)
        ax.text(mc_ang, inner_r - 0.07, "MC", ha="center", va="center",
                fontsize=12, color="purple", fontweight="bold", zorder=4)
    except Exception:
        pass  # якщо з якоїсь причини немає кутів — не валимо малювання

    # --- Планети (точні довготи) ---
    # Розміщуємо маркери на колі r=0.90, символи трохи зовні, щоб не перекривались
    planet_r = ring_r - 0.10
    label_r  = ring_r - 0.04

    for obj in chart.objects:
        if obj.id not in PLANET_SYMBOLS:
            continue
        ang = deg_to_rad(obj.lon)
        col = PLANET_COLORS.get(obj.id, "black")
        # маркер
        ax.scatter(ang, planet_r, s=120, color=col, zorder=5)
        # символ
        ax.text(ang, label_r, PLANET_SYMBOLS[obj.id],
                ha="center", va="center", fontsize=16, color=col, zorder=6)

    # --- Аспекти (лінії між планетами) ---
    aspects_data = compute_aspects(chart)
    for asp in aspects_data:
        try:
            p1 = chart.getObject(asp["planet1"])
            p2 = chart.getObject(asp["planet2"])
        except Exception:
            # fallback, якщо getObject не знаходить: підбираємо з chart.objects
            p1 = next((o for o in chart.objects if o.id == asp["planet1"]), None)
            p2 = next((o for o in chart.objects if o.id == asp["planet2"]), None)
        if not p1 or not p2:
            continue
        a1, a2 = deg_to_rad(p1.lon), deg_to_rad(p2.lon)
        ax.plot([a1, a2], [planet_r, planet_r], color=asp["color"], lw=1.4, alpha=0.9, zorder=4)

    # --- Логотип у секторі Скорпіона: білим на бордо ---
    # Скорпіон починається на 210°. Розмістимо трохи зовні кільця знаків.
    scorpio_angle = deg_to_rad(210)
    ax.text(
        scorpio_angle, ring_r + 0.09, "Albireo Daria ♏",
        ha="center", va="center", fontsize=14, color="white", zorder=6,
        bbox=dict(boxstyle="round,pad=0.35", fc="#6a1b2c", ec="none")
    )

    # --- Легенди (планети та аспекти) ---
    # Планети
    planet_handles, planet_labels = [], []
    for pid, sym in PLANET_SYMBOLS.items():
        col = PLANET_COLORS.get(pid, "#222")
        planet_handles.append(plt.Line2D([0], [0], marker="o", color="w",
                                         markerfacecolor=col, markersize=8, lw=0))
        planet_labels.append(f"{sym} {pid}")
    leg1 = ax.legend(planet_handles, planet_labels, loc="lower center",
                     bbox_to_anchor=(0.5, -0.08), fontsize=8, ncol=4, frameon=False,
                     title="Планети/точки", title_fontsize=9)
    ax.add_artist(leg1)

    # Аспекти
    asp_handles, asp_labels = [], []
    for atype, (_, col, _) in ASPECTS.items():
        asp_handles.append(plt.Line2D([0, 1], [0, 0], color=col, lw=2))
        asp_labels.append(atype.capitalize())
    leg2 = ax.legend(asp_handles, asp_labels, loc="lower center",
                     bbox_to_anchor=(0.5, -0.14), fontsize=8, ncol=5, frameon=False,
                     title="Аспекти", title_fontsize=9)
    ax.add_artist(leg2)

    plt.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

# -------------------- API --------------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()

        data = request.json or {}
        name = data.get("name", "Person")
        date = data.get("date")
        time = data.get("time")
        place = data.get("place")

        if not (date and time and place):
            return jsonify({"error": "Потрібні поля: date, time, place"}), 400

        # Геолокація
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400

        # Таймзона
        tz_str = tf.timezone_at(lat=location.latitude, lng=location.longitude) or "UTC"
        tz = pytz.timezone(tz_str)

        # Локальний час
        try:
            naive_dt = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return jsonify({"error": "Невірний формат дати/часу. Очікується '%Y-%m-%d %H:%M'"}), 400

        local_dt = tz.localize(naive_dt)
        offset_hours = local_dt.utcoffset().total_seconds() / 3600

        # Flatlib datetime + Placidus
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(location.latitude, location.longitude)
        chart = Chart(fdate, pos, hsys="Placidus")

        # Кеш-ключ
        key = md5_key(f"{name}|{date}|{time}|{place}|{tz_str}")
        img_path = os.path.join(CACHE_DIR, f"{key}.png")
        json_path = os.path.join(CACHE_DIR, f"{key}.json")

        # Якщо вже є — повертаємо з кешу
        if os.path.exists(img_path) and os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            return jsonify({**cached, "chart_url": f"/cache/{key}.png"})

        # Обчислити аспекти та намалювати карту
        aspects_json = compute_aspects(chart)
        draw_chart(chart, img_path)

        payload = {
            "name": name,
            "date": date,
            "time": time,
            "place": place,
            "timezone": tz_str,
            "aspects_json": aspects_json,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

        return jsonify({**payload, "chart_url": f"/cache/{key}.png"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Видача кешу (PNG)
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

# Health check
@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Запуск локально
    app.run(host="0.0.0.0", port=8080)