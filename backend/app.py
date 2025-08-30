
# app.py — професійна натальна карта (Placidus), кеш PNG/JSON, дугові підписи, лого, DMS, ASC/MC/IC/DSC
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
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL_DAYS = 30

geolocator = Nominatim(user_agent="albireo_astro_app")
tf = TimezoneFinder()

# ----------------- Конфіг -----------------
ZODIAC_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
ZODIAC_NAMES   = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                  "Стрілець","Козеріг","Водолій","Риби"]

# М’які пастельні: будинки
HOUSE_COLORS = [
    "#fde0dc", "#f8bbd0", "#e1bee7", "#d1c4e9",
    "#c5cae9", "#bbdefb", "#b3e5fc", "#b2ebf2",
    "#b2dfdb", "#c8e6c9", "#dcedc8", "#f0f4c3"
]

# Планети, символи, кольори (світлі, контрастні)
PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "North Node":"☊","South Node":"☋","Ascendant":"ASC","MC":"MC",
    "Pars Fortuna":"⚶"
}
PLANET_COLORS = {
    "Sun":"#f6c90e","Moon":"#c0c0c0","Mercury":"#7d7d7d","Venus":"#e88fb4","Mars":"#e55d5d",
    "Jupiter":"#f3a33c","Saturn":"#b78b68","Uranus":"#69d2e7","Neptune":"#6a9bd1","Pluto":"#3d3d3d",
    "Ascendant":"#2ecc71","MC":"#8e44ad"
}

# Аспекти (кут, орб, колір — світлі, читабельні)
ASPECTS_DEF = {
    "conjunction": {"angle": 0,   "orb": 8, "color": "#bbbbbb"},
    "sextile":     {"angle": 60,  "orb": 6, "color": "#a7d6a7"},
    "square":      {"angle": 90,  "orb": 6, "color": "#f3a7a7"},
    "trine":       {"angle": 120, "orb": 8, "color": "#9ec6f3"},
    "opposition":  {"angle": 180, "orb": 8, "color": "#8c2d3b"},
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
    # Приймає десяткові градуси, повертає 'D°M'S"'
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
    for _ in range(retries + 1):
        try:
            loc = geolocator.geocode(place, timeout=timeout)
            if loc:
                return float(loc.latitude), float(loc.longitude)
            if "," not in place and _ == 0:
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
                        "type": name,
                        "angle": round(diff, 2),
                        "angle_dms": deg_to_dms(diff),
                        "color": cfg["color"]
                    })
                    break
    return results

# ----------------- Малювання карти -----------------
def draw_natal_chart(chart, aspects_list, save_path, name_for_center=None, logo_text="Albireo Daria^"):
    try:
        fig = plt.figure(figsize=(12, 12))
        ax = plt.subplot(111, polar=True)
        ax.set_theta_zero_location("W")
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 1.35)
        ax.set_xticks([]); ax.set_yticks([])
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        plt.rcParams["font.family"] = "DejaVu Sans"

              # 1) Сектори будинків (Placidus) або fallback рівні 30°
        try:
            for i in range(1, 13):
                cusp1 = get_house_lon(chart, i)
                cusp2 = get_house_lon(chart, (i % 12) + 1)
                if cusp1 is None or cusp2 is None:
                    raise RuntimeError("house cusps not available")
                start_deg = cusp1 % 360
                end_deg = cusp2 % 360
                if (end_deg - start_deg) <= 0:
                    end_deg += 360
                theta_start = np.deg2rad(start_deg)
                theta_end = np.deg2rad(end_deg)
                width = abs(theta_end - theta_start)
                ax.bar(
                    x=(theta_start + theta_end) / 2,
                    height=1.10, width=width, bottom=0.00,
                    color=HOUSE_COLORS[(i-1) % 12], alpha=0.28,
                    edgecolor="white", linewidth=0.6, zorder=0
                )
                # вершина дому
                ax.plot([np.deg2rad(start_deg), np.deg2rad(start_deg)], [0.15, 1.18], color="#888888", lw=0.8, zorder=2)
        except Exception:
            # fallback рівні 30°
            for i in range(12):
                start = i * 30
                theta_start = np.deg2rad(start)
                theta_end = np.deg2rad(start + 30)
                width = abs(theta_end - theta_start)
                ax.bar(
                    x=(theta_start + theta_end) / 2,
                    height=1.10, width=width, bottom=0.00,
                    color=HOUSE_COLORS[i % 12], alpha=0.22,
                    edgecolor="white", linewidth=0.6, zorder=0
                )
                ax.plot([np.deg2rad(start), np.deg2rad(start)], [0.15, 1.18], color="#888888", lw=0.8, zorder=2)


        # 2) Бордове кільце Зодіаку + символи та дугові підписи
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i * 30
            theta_start = np.deg2rad(start)
            theta_end = np.deg2rad(start + 30)
            width = abs(theta_end - theta_start)
            ax.bar(x=(theta_start + theta_end) / 2, height=0.12, width=width, bottom=1.18,
                   color="#6a1b2c", edgecolor="white", linewidth=1.2, zorder=3)
            ax.plot([theta_start, theta_start], [1.18, 1.30], color="white", lw=1.2, zorder=4)

            center_deg = start + 15
            theta_c = np.deg2rad(center_deg)
            text_rot = -(center_deg)
            if sym == "♏":
                ax.text(theta_c, 1.225, logo_text, fontsize=13, ha="center", va="center",
                        color="#FFD700", fontweight="bold", rotation=text_rot, rotation_mode="anchor", zorder=6)
            else:
                ax.text(theta_c, 1.205, sym, fontsize=20, ha="center", va="center",
                        color="white", fontweight="bold", rotation=text_rot, rotation_mode="anchor", zorder=5)
                ax.text(theta_c, 1.24, ZODIAC_NAMES[i], fontsize=9, ha="center", va="center",
                        color="white", rotation=text_rot, rotation_mode="anchor", zorder=5)

            # дугові внутрішні риски 5° (в межах знаку)
            for deg_mark in range(0, 31, 5):
                theta_deg = np.deg2rad(start + deg_mark)
                r_start = 1.15
                r_end = 1.18 if deg_mark % 10 == 0 else 1.16
                ax.plot([theta_deg, theta_deg], [r_start, r_end], color="#6a1b2c", lw=1, zorder=2)

        # +++ ДОДАНО: Зовнішня градуйовка кожні 30° і 10° з цифрами і рисками + DMS +++
        for deg in range(0, 360, 10):
            th = np.deg2rad(deg)
            r0 = 1.15
            r1 = 1.18 if deg % 30 == 0 else 1.165
            ax.plot([th, th], [r0, r1], color="black", lw=1.0 if deg % 30 == 0 else 0.6, zorder=4)
            if deg % 30 == 0:
                ax.text(th, 1.205, f"{deg}°", fontsize=8, ha="center", va="center", color="black")
                ax.text(th, 1.235, deg_to_dms(deg), fontsize=7, ha="center", va="center", color="gray")

         # 4) Центральне кільце + бордовий диск з ім'ям
        inner_ring = plt.Circle((0, 0), 0.14, color="#f5f5f5", zorder=1, fill=True, ec="#dddddd", lw=0.5)
        ax.add_artist(inner_ring)
        center_circle = plt.Circle((0, 0), 0.10, color="#800000", zorder=10)
        ax.add_artist(center_circle)
        if name_for_center:
            ax.text(0, 0, name_for_center, color="white", ha="center", va="center",
                    fontsize=10, fontweight="bold", zorder=11)

        # 5) Номери домів (по Placidus або fallback)
        try:
            for i in range(1, 13):
                cusp1 = get_house_lon(chart, i)
                cusp2 = get_house_lon(chart, (i % 12) + 1)
                if cusp1 is None or cusp2 is None:
                    raise RuntimeError
                start = cusp1 % 360
                end = cusp2 % 360
                diff = (end - start) % 360
                mid = (start + diff / 2.0) % 360
                th_mid = np.deg2rad(mid)
                ax.text(th_mid, 0.14, str(i), fontsize=9, ha="center", va="center",
                        color="#6a1b2c", fontweight="bold", zorder=7)
        except Exception:
            for i in range(12):
                th_mid = np.deg2rad(i*30 + 15)
                ax.text(th_mid, 0.14, str(i+1), fontsize=9, ha="center", va="center",
                        color="#6a1b2c", fontweight="bold", zorder=7)

        # 6) ASC/MC/DSC/IC маркери
        try:
            asc_obj = chart.get(const.ASC)
            mc_obj = chart.get(const.MC)
            asc = getattr(asc_obj, "lon", None)
            mc  = getattr(mc_obj, "lon", None)
            if asc is not None and mc is not None:
                asc = asc % 360
                mc = mc % 360
                dsc = (asc + 180) % 360
                ic  = (mc  + 180) % 360
                angles = [("ASC", asc, "#2ecc71"), ("MC", mc, "#8e44ad"),
                          ("DSC", dsc, "#2ecc71"), ("IC", ic, "#8e44ad")]
                for lab, ang, col in angles:
                    th = np.deg2rad(ang)
                    ax.plot([th, th], [1.00, 1.15], color=col, lw=2.0, zorder=6)
                    ax.text(th, 1.02, lab, fontsize=9, ha="center", va="center",
                            color=col, fontweight="bold", zorder=6, rotation=-ang, rotation_mode="anchor")
        except Exception:
            pass

        # 7) Планети: великий символ + DMS підпис
        # збираємо позиції для аспектів
        planet_positions = {}
        for obj in chart.objects:
            try:
                oid = getattr(obj, "id", None)
                if oid in PLANET_SYMBOLS:
                    # деякі flatlib об'єкти можуть мати .lon або .signlon
                    lon = getattr(obj, "lon", None)
                    if lon is None:
                        lon = getattr(obj, "signlon", None)
                    if lon is None:
                        continue
                    lon = float(lon) % 360
                    th = np.deg2rad(lon)
                    r = 0.90
                    sym = PLANET_SYMBOLS[oid]
                    col = PLANET_COLORS.get(oid, "black")
                    # великий символ
                    ax.text(th, r, sym, fontsize=20, ha="center", va="center", color=col, zorder=8)
                    # підпис з DMS під символом
                    ax.text(th, r - 0.07, f"{oid} {deg_to_dms(lon)}", fontsize=8,
                            ha="center", va="center", color=col, zorder=8)
                    planet_positions[oid] = (th, r)
            except Exception:
                continue

        # 8) Аспекти: кольорові дуги + легенда
        r_line = 0.82  # радіус дуг аспектів
        legend_items = []

        for asp in aspects_list:
            try:
                p1_id = asp["planet1"]
                p2_id = asp["planet2"]
                lon1, lon2 = None, None
                # знайти lon за id
                for o in chart.objects:
                    oid = getattr(o, "id", None)
                    if oid == p1_id:
                        lon1 = getattr(o, "lon", getattr(o, "signlon", None))
                    if oid == p2_id:
                        lon2 = getattr(o, "lon", getattr(o, "signlon", None))
                if lon1 is None or lon2 is None:
                    continue

                th1 = np.deg2rad(float(lon1) % 360)
                th2 = np.deg2rad(float(lon2) % 360)
                # коротка дуга
                d = ((th2 - th1 + np.pi) % (2*np.pi)) - np.pi
                steps = max(12, int(abs(d)/(np.pi/180)*2))
                thetas = np.linspace(th1, th1 + d, steps)
                rs = np.full_like(thetas, r_line)
                ax.plot(thetas, rs, color=asp.get("color", "#777777"), lw=1.6, alpha=0.95, zorder=5)
                legend_items.append((asp["type"], asp.get("color", "#777777")))
            except Exception:
                continue

        # Унікальна легенда
        legend_items = list({(n, c) for n, c in legend_items})
        for name, color in legend_items:
            ax.plot([], [], color=color, lw=3, label=name)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=len(legend_items))         # 9) Логотип-дуга поруч зі знаком Скорпіона вже намальований над написами.
            
        # 10) Збереження картинки
       
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

        # Local datetime -> flatlib Datetime (offset у годинах!)
        try:
            naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            local_dt = tz.localize(naive)
            offset_hours = (local_dt.utcoffset().total_seconds() / 3600.0) if local_dt.utcoffset() else 0.0
        except Exception as e:
            return jsonify({"error": f"Невірний формат date/time: {str(e)}"}), 400

        # flatlib Datetime за формою 'YYYY/MM/DD' та 'HH:MM' і offset_hours
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)

        # Placidus (hsys='P'), fallback — як є
        try:
            chart = Chart(fdate, pos, hsys='P')
        except Exception:
            chart = Chart(fdate, pos)

        # Аспекти
        aspects_json = compute_aspects_manual(chart.objects)

        # Малювання PNG (і створення кеш-файла)
        try:
            draw_natal_chart(chart, aspects_json, png_path, name_for_center=name, logo_text="Albireo Daria^")
        except Exception as e:
            base_url = request.host_url.rstrip("/")
            out = {
                "name": name, "date": date_str, "time": time_str,
                "place": place, "timezone": tz_str,
                "aspects_json": aspects_json,
                "chart_url": None,
                "warning": f"Помилка при малюванні картинки: {str(e)}"
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            return jsonify(out), 200

        # JSON-відповідь + кеш JSON
        base_url = request.host_url.rstrip("/")
        out = {
            "name": name, "date": date_str, "time": time_str,
            "place": place, "timezone": tz_str,
            "aspects_json": aspects_json,
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
    app.run(host="0.0.0.0", port=port, debug=True)
    