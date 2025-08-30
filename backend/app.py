# app.py — повний робочий сервер для натальної карти (Placidus, кеш, PNG, аспекти, DMS)
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

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz
import numpy as np

from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# ----------------------------------------
# Глобальні об'єкти та конфіг
# ----------------------------------------
geolocator = Nominatim(user_agent="my_astrology_app")
tf = TimezoneFinder()

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL_DAYS = 30

# Планети/символи/кольори
PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "North Node":"☊","South Node":"☋","Ascendant":"ASC","MC":"MC",
    "Pars Fortuna":"⚶"
}
PLANET_COLORS = {
    "Sun":"gold","Moon":"silver","Mercury":"darkgray","Venus":"palevioletred",
    "Mars":"red","Jupiter":"orange","Saturn":"brown",
    "Uranus":"deepskyblue","Neptune":"blue","Pluto":"black",
    "Ascendant":"green","MC":"purple"
}

ASPECTS_DEF = {
    "conjunction": {"angle": 0, "orb": 8, "color": "#cccccc"},
    "sextile": {"angle": 60, "orb": 6, "color": "#f7eaea"},
    "square": {"angle": 90, "orb": 6, "color": "#f59ca9"},
    "trine": {"angle": 120, "orb": 8, "color": "#d4a5a5"},
    "opposition": {"angle": 180, "orb": 8, "color": "#4a0f1f"},
}

ZODIAC_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
ZODIAC_NAMES = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                "Стрілець","Козеріг","Водолій","Риби"]

# ----------------------------------------
# Утиліти
# ----------------------------------------
def cleanup_cache(days: int = CACHE_TTL_DAYS):
    """Видаляє файли в CACHE_DIR старші ніж days днів."""
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
    """Приймає десяткові градуси, повертає 'D°M'S\"' (ціле градуси, хвилини, секунди)."""
    # нормалізуємо 0..360
    angle = float(angle_float) % 360.0
    d = int(angle)
    m_f = (angle - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    # виправити випадок коли s == 60
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d = (d + 1) % 360
    return f"{d}°{m}'{s}\""

def geocode_place(place, retries=2, timeout=8):
    """Повертає (lat, lon) або (None, None) — з retry на таймаут."""
    for _ in range(retries+1):
        try:
            loc = geolocator.geocode(place, timeout=timeout)
            if loc:
                return loc.latitude, loc.longitude
            else:
                return None, None
        except GeocoderTimedOut:
            continue
        except Exception:
            break
    return None, None

# ----------------------------------------
# Обчислення аспектів вручну (по довготам)
# ----------------------------------------
def compute_aspects_manual(objects):
    results = []
    objs = [o for o in objects if getattr(o, "id", None) in PLANET_SYMBOLS]
    for i in range(len(objs)):
        for j in range(i+1, len(objs)):
            p1 = objs[i]; p2 = objs[j]
            a1 = getattr(p1, "lon", 0) % 360
            a2 = getattr(p2, "lon", 0) % 360
            diff = abs(a1 - a2)
            if diff > 180:
                diff = 360 - diff
            for name, cfg in ASPECTS_DEF.items():
                target = cfg["angle"]
                orb = cfg["orb"]
                if abs(diff - target) <= orb:
                    results.append({
                        "planet1": getattr(p1, "id", str(p1)),
                        "planet1_symbol": PLANET_SYMBOLS.get(getattr(p1, "id", ""), getattr(p1, "id", "")),
                        "planet2": getattr(p2, "id", str(p2)),
                        "planet2_symbol": PLANET_SYMBOLS.get(getattr(p2, "id", ""), getattr(p2, "id", "")),
                        "type": name,
                        "angle": round(diff, 2),
                        "angle_dms": deg_to_dms(round(diff, 6)),
                        "color": cfg["color"]
                    })
                    break
    return results

# ----------------------------------------
# Малювання натальної карти
# ----------------------------------------
def draw_natal_chart(chart, aspects_list, save_path, logo_text="Albireo Daria ♏"):
    try:
        figsize = (12, 12)
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111, polar=True)
        ax.set_theta_direction(-1)           # по годиннику
        ax.set_theta_offset(math.pi/2)       # 0° зверху (поточна система використовує 90 - lon)
        ax.set_ylim(0, 1.4)
        ax.set_xticks([]); ax.set_yticks([])
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        unicode_font = "DejaVu Sans"
        plt.rcParams["font.family"] = unicode_font

        # Пастельні кольори секторів будинків
        house_colors = [
            "#fde0dc", "#f8bbd0", "#e1bee7", "#d1c4e9",
            "#c5cae9", "#bbdefb", "#b3e5fc", "#b2ebf2",
            "#b2dfdb", "#c8e6c9", "#dcedc8", "#f0f4c3"
        ]

        # Сектори будинків (Placidus) — якщо chart.houses доступні
        try:
            # Chart.houses індексуються 1..12 або 0..11 залежить від impl; пробуємо 0..11
            for i in range(12):
                # можливі варіанти доступу — намагаємось без помилок
                try:
                    cusp1 = chart.houses[i].lon
                    cusp2 = chart.houses[(i+1) % 12].lon
                except Exception:
                    # інша API: chart.houses.get(i+1)
                    try:
                        cusp1 = chart.houses.get(i+1).lon
                        cusp2 = chart.houses.get((i+1) % 12 + 1).lon
                    except Exception:
                        raise

                start_deg = cusp1 % 360
                end_deg = cusp2 % 360
                if end_deg <= start_deg:
                    end_deg += 360

                theta_start = math.radians(90 - start_deg)
                theta_end = math.radians(90 - end_deg)
                width = abs(theta_end - theta_start)

                ax.bar(
                    x=(theta_start + theta_end) / 2,
                    height=1.4, width=width, bottom=0,
                    color=house_colors[i % len(house_colors)],
                    edgecolor="white", linewidth=0.6, alpha=0.33, zorder=0
                )
        except Exception as e:
            # якщо не вдається — малюємо стандартні 12 секторів рівного розміру
            for i in range(12):
                start_deg = i * 30
                theta_start = math.radians(90 - start_deg)
                theta_end = math.radians(90 - (start_deg + 30))
                width = abs(theta_end - theta_start)
                ax.bar(x=(theta_start + theta_end) / 2, height=1.4, width=width, bottom=0,
                       color=house_colors[i % len(house_colors)], edgecolor="white", linewidth=0.6, alpha=0.25, zorder=0)

        # Бордові дуги / символи знаків зодіаку
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start_deg = i * 30
            end_deg = start_deg + 30
            theta_start = math.radians(90 - start_deg)
            theta_end = math.radians(90 - end_deg)
            width = abs(theta_end - theta_start)

            ax.bar(x=(theta_start + theta_end) / 2,
                   height=1.32, width=width, bottom=1.18,
                   color="#6a1b2c", edgecolor="white", linewidth=1.2, zorder=1)

            center_deg = start_deg + 15
            theta = math.radians(90 - center_deg)
            ax.text(theta, 1.25, sym, fontsize=20, ha="center", va="center",
                    color="white", fontfamily=unicode_font, fontweight="bold", zorder=2)
            ax.text(theta, 1.34, ZODIAC_NAMES[i], fontsize=9, ha="center", va="center",
                    color="white", fontfamily=unicode_font, zorder=2)

            # Градуйровка 0-30° кожні 5° всередині знаку
            for deg_mark in range(0, 31, 5):
                theta_deg = i*30 + deg_mark
                theta_rad = math.radians(90 - theta_deg)
                r_start = 1.15
                r_end = 1.18 if deg_mark % 10 == 0 else 1.16
                ax.plot([theta_rad, theta_rad], [r_start, r_end], color="#6a1b2c", lw=1, zorder=2)

        # Центральне бордове коло з ім'ям/датою
        try:
            circle = plt.Circle((0,0), 0.2, color="#6a1b2c", zorder=10)
            ax.add_artist(circle)
            # chart.date може бути Datetime — намагаємось взяти human-readable
            date_label = getattr(chart, "date", None)
            if date_label is None:
                label = ""
            else:
                # на flatlib Datetime.date може бути рядком або об'єктом — спростимо
                try:
                    # якщо є .date або .strftime
                    label = getattr(chart.date, "date", str(chart.date))
                except Exception:
                    label = str(chart.date)
            ax.text(0, 0, label, fontsize=12, ha="center", va="center", color="white", fontweight="bold")
        except Exception:
            pass

        # Градуйровка зовнішнього кола: кожні 10° (помітні кожні 30° з цифрою)
        for deg in range(0, 360, 10):
            theta = math.radians(90 - deg)
            r_start = 1.15
            r_end = 1.18 if deg % 30 == 0 else 1.16
            ax.plot([theta, theta], [r_start, r_end], color="black", lw=0.7, zorder=2)
            if deg % 30 == 0:
                ax.text(theta, 1.21, str(deg), fontsize=8, ha="center", va="center", color="black")

        # Планети: символ + підпис (DMS)
        for obj in chart.objects:
            try:
                oid = getattr(obj, "id", None)
                if oid in PLANET_SYMBOLS:
                    angle_deg = obj.lon % 360
                    theta = math.radians(90 - angle_deg)
                    r = 0.95
                    symbol = PLANET_SYMBOLS[oid]
                    color = PLANET_COLORS.get(oid, "black")
                    ax.text(theta, r, symbol, fontsize=16, ha="center", va="center",
                            color=color, fontfamily=unicode_font, zorder=5)
                    ax.text(theta, r - 0.06, f"{oid} {deg_to_dms(obj.lon)}",
                            fontsize=8, ha="center", va="center", color=color, zorder=5)
            except Exception:
                continue

        # Аспекти — лінії між позиціями планет
        for asp in aspects_list:
            try:
                p1 = next(o for o in chart.objects if getattr(o, "id", None) == asp["planet1"])
                p2 = next(o for o in chart.objects if getattr(o, "id", None) == asp["planet2"])
                angle1 = p1.lon % 360
                angle2 = p2.lon % 360
                theta1 = math.radians(90 - angle1)
                theta2 = math.radians(90 - angle2)
                ax.plot([theta1, theta2], [0.95, 0.95], color=asp["color"], linewidth=1.2, zorder=3, alpha=0.9)
            except Exception:
                continue

        # Логотип-дуга поруч зі знаком Скорпіона (приблизно центр знаку)
        try:
            sc_center_deg = 210
            sc_theta = math.radians(90 - sc_center_deg)
            ax.text(sc_theta, 1.27, logo_text, fontsize=14, ha="center", va="center",
                    color="white", fontfamily=unicode_font, fontweight="bold",
                    bbox=dict(facecolor="#6a1b2c", edgecolor="none", pad=5, boxstyle="round,pad=0.4"), zorder=6)
        except Exception:
            pass

        # Збереження
        try:
            plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        finally:
            plt.close(fig)

    except Exception as e:
        print("Error in draw_natal_chart:", e)
        traceback.print_exc()
        raise

# ----------------------------------------
# Endpoint: /generate
# ----------------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()

        data = request.get_json() or {}
        name = data.get("name", data.get("firstName", "Person"))
        date_str = data.get("date")    # YYYY-MM-DD
        time_str = data.get("time")    # HH:MM
        place = data.get("place")

        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date (YYYY-MM-DD), time (HH:MM) та place (рядок)"}), 400

        key = cache_key(name, date_str, time_str, place)
        json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_cache_path = os.path.join(CACHE_DIR, f"{key}.png")

        # Якщо в кеші — повернути
        if os.path.exists(json_cache_path) and os.path.exists(png_cache_path):
            try:
                mtime = dt.fromtimestamp(os.path.getmtime(json_cache_path))
                if dt.now() - mtime <= timedelta(days=CACHE_TTL_DAYS):
                    with open(json_cache_path, "r", encoding="utf-8") as f:
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

        # Таймзона (fallback UTC)
        try:
            tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            tz = pytz.timezone(tz_str)
        except Exception:
            tz_str = "UTC"
            tz = pytz.timezone("UTC")

        # Парсимо local datetime і обчислюємо offset в годинах для flatlib Datetime
        try:
            naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            local_dt = tz.localize(naive)
            # offset in hours (may be fractional)
            offset_hours = local_dt.utcoffset().total_seconds() / 3600.0
        except Exception as e:
            return jsonify({"error": f"Невірний формат date/time: {str(e)}"}), 400

        # Створюємо Datetime для flatlib — формат YYYY/MM/DD у перших арг.
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        # Створюємо Chart (Placidus) з fallback
        try:
            chart = Chart(fdate, pos, hsys=getattr(const, "HOUSES_PLACIDUS", None) or "Placidus")
        except Exception:
            chart = Chart(fdate, pos)

        # Обчислення аспектів
        aspect_list = compute_aspects_manual(chart.objects)

        # Малюємо та зберігаємо картинку
        try:
            draw_natal_chart(chart, aspect_list, png_cache_path)
        except Exception as e:
            # Якщо не згенерувалась картинка — повернути JSON з warning
            result = {
                "name": name, "date": date_str, "time": time_str,
                "place": place, "timezone": tz_str,
                "aspects_json": aspect_list, "chart_url": None,
                "warning": f"Помилка при малюванні картинки: {str(e)}"
            }
            with open(json_cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return jsonify(result), 200

        # Підготувати результат і кешувати JSON
        base_url = request.host_url.rstrip("/")
        out = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "aspects_json": aspect_list,
            "chart_url": f"{base_url}/cache/{key}.png"
        }
        with open(json_cache_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        return jsonify(out)

    except Exception as e:
        print("Unhandled error in /generate:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ----------------------------------------
# Файловий ендпоінт для картинок
# ----------------------------------------
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)