# app.py — робоча, обережна та сумісна версія
import os
import math
import json
import time
import hashlib
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# optional interactive cursor (if installed)
try:
    import mplcursors
    HAS_MPLCURSORS = True
except Exception:
    HAS_MPLCURSORS = False

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# flatlib
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
# const and aspects usage – будемо використовувати мінімально, вручну обчислюємо аспекти
from flatlib import const

app = Flask(__name__)
CORS(app)

# Кеш
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Очистка кешу старше 30 днів
def cleanup_cache(days: int = 30):
    now_ts = time.time()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        if os.path.isfile(fpath):
            if now_ts - os.path.getmtime(fpath) > days * 24 * 3600:
                try:
                    os.remove(fpath)
                except Exception:
                    pass

# Викликаємо на старті
cleanup_cache()

# Геокодер + timezone finder (реюзимо інстанси)
geolocator = Nominatim(user_agent="astro_app_v1")
tf = TimezoneFinder()

# Кольори аспектів
ASPECTS_DEF = {
    "conjunction": {"angle": 0, "orb": 8, "color": "#cccccc"},
    "sextile": {"angle": 60, "orb": 6, "color": "#f7eaea"},
    "square": {"angle": 90, "orb": 6, "color": "#8b8b8b"},
    "trine": {"angle": 120, "orb": 8, "color": "#d4a5a5"},
    "opposition": {"angle": 180, "orb": 8, "color": "#4a0f1f"},
}

# Символи планет / імена, кольори
PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆",
    "Pluto": "♇", "North Node": "☊", "South Node": "☋",
    "Ascendant": "ASC", "MC": "MC", "Pars Fortuna": "⚶", "Syzygy": "☌"
}
PLANET_COLORS = {
    "Sun": "gold", "Moon": "silver", "Mercury": "darkorange", "Venus": "deeppink",
    "Mars": "red", "Jupiter": "royalblue", "Saturn": "brown", "Uranus": "deepskyblue",
    "Neptune": "mediumslateblue", "Pluto": "purple", "Ascendant": "green", "MC": "black"
}

# Допоміжні функції
def cache_key(name, date_str, time_str, place):
    key = f"{name}|{date_str}|{time_str}|{place}"
    return hashlib.md5(key.encode()).hexdigest()

def decdeg_to_dms(deg):
    """Перетворює десяткові градуси в (deg, min, sec)"""
    sign = 1 if deg >= 0 else -1
    deg_abs = abs(deg)
    d = int(deg_abs)
    m = int((deg_abs - d) * 60)
    s = round((deg_abs - d - m/60) * 3600, 2)
    d = d * sign
    return d, m, s

def deg_to_str_dms(deg):
    d, m, s = decdeg_to_dms(deg)
    return f"{d}°{m:02d}'{int(s):02d}\""

# Обчислення аспектів вручну (по довготам)
def compute_aspects_manual(objects):
    results = []
    # беремо список об'єктів, які мають lon і id
    objs = [o for o in objects if hasattr(o, "lon") and hasattr(o, "id")]
    for i in range(len(objs)):
        for j in range(i+1, len(objs)):
            p1 = objs[i]; p2 = objs[j]
            a1 = p1.lon % 360
            a2 = p2.lon % 360
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
                        "color": cfg["color"]
                    })
                    break
    return results

# Популярний набір об'єктів для відображення (за flatlib ними зазвичай id-значення такі як 'Sun', 'Moon', ...)
DISPLAY_ORDER = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","North Node","South Node","Ascendant","MC","Pars Fortuna","Syzygy"]

# Малюємо натальну карту
def draw_natal_chart(chart, aspects_list, save_path, logo_text="Albireo Daria ♏"):
    """
    Малює професійну натальну карту:
    - великі круги/дуги для знаків зодіаку
    - пастельні сектори будинків (Placidus cusps)
    - планети у правильних позиціях з символами та підписами (deg/min/sec)
    - лінії аспектів кольорові
    - Asc і MC підписані
    - логотип у секторі Скорпіона (скопійовано як білий текст на бордовому тлі)
    """
    # Параметри фігури
    figsize = (12, 12)
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111, polar=True)
    ax.set_theta_direction(-1)  # clockwise
    ax.set_theta_offset(math.pi/2)  # 0° = top
    ax.set_ylim(0, 1.4)
    ax.set_xticks([]); ax.set_yticks([])
    # фон чистий (вимкнемо темний фон по користувацькому запиту)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # 1) Знаки зодіаку — за колом, кожен знак 30°
    zodiac_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    # Put zodiac labels on outer ring (center of each 30° segment)
    for i, sym in enumerate(zodiac_symbols):
        # center angle of sign i (Aries=0..)
        center_deg = (i * 30) + 15  # middle of sign
        theta = math.radians(90 - center_deg)  # convert to our polar system
        r = 1.18
        ax.text(theta, r, sym, fontsize=20, ha="center", va="center", color="#6a1b2c")

    # 2) Будинки (Placidus cusps) — беремо список будинків з chart.houses (fallback-friendly)
    houses = []
    try:
        # chart.houses в flatlib може бути ітерованим
        houses = list(chart.houses)
    except Exception:
        # fallback: спробуємо дістати по номерам через chart.get
        houses = []
        for n in range(1,13):
            try:
                h = chart.get(f"H{n}")
                if h:
                    houses.append(h)
            except Exception:
                pass

    # Якщо немає cusps — спробуємо взяти кути будинків з chart.houses.lon якщо можна
    if not houses:
        try:
            # інша можливість: Chart пропонує метод houses.cusps? - на випадок
            hlist = getattr(chart, "houses", None)
            if hlist:
                houses = list(hlist)
        except Exception:
            houses = []

    # Побудова пастельних секторів будинків по кутам cusps
    # Ми беремо lon кожного дому (довгота cusp в градусах)
    house_lons = []
    for idx, h in enumerate(houses):
        lon = None
        if hasattr(h, "lon"):
            lon = getattr(h, "lon")
        elif isinstance(h, (int, float)):
            lon = float(h)
        if lon is not None:
            house_lons.append(lon % 360)
    # Якщо не вдалося витягнути — зробимо рівні 30° сектора (гарантія)
    if len(house_lons) != 12:
        house_lons = [(i*30) % 360 for i in range(12)]

    # Sort by angle (house cusps may not be in order)
    # But we need them in natural house order; کوشش: assume given order is house1..house12; if not, sort by value
    # We'll use the sequence house_lons as is (should be house1..house12 or fallback)
    # For drawing sectors we need start and end angles in radians
    for i in range(12):
        start_deg = house_lons[i]
        end_deg = house_lons[(i+1) % 12]
        # Ensure correct direction: compute angular span going forward
        span = (end_deg - start_deg) % 360
        if span <= 0:
            span += 360
        theta = math.radians(90 - start_deg)
        width = math.radians(span)
        # pastel color for houses
        color = plt.cm.Pastel1(i/12)
        ax.bar(theta, 0.9, width=width, bottom=0.25, color=color, alpha=0.25, align="edge", edgecolor="none")

        # label number of house on inner ring at middle of sector
        mid_deg = (start_deg + span/2) % 360
        mid_theta = math.radians(90 - mid_deg)
        ax.text(mid_theta, 0.27, str(i+1), fontsize=10, ha="center", va="center", color="#6a1b2c")

    # 3) Градуйровка по колу (кожні 30°, і дрібніше кожні 10°)
    for deg in range(0, 360, 10):
        theta = math.radians(90 - deg)
        r = 1.0
        if deg % 30 == 0:
            # крупніші риски з підписом
            ax.plot([theta, theta], [0.98, 1.02], lw=1.2, color="#444")
            # degree label (на зовнішньому діаметрі)
            ax.text(theta, 1.07, f"{deg}°", fontsize=8, ha="center", va="center", color="#333")
        else:
            ax.plot([theta, theta], [0.99, 1.01], lw=0.6, color="#888")

    # 4) Планети: по chart.objects беремо id і lon. Розміщуємо "3D"-шарики (імітація світлотіні)
    # Для більш "3D" вигляду використовуємо два маркери: тінь і головний колір
    for o in chart.objects:
        # деякі об'єкти можуть не мати lon/id — пропускаємо
        if not hasattr(o, "lon") or not hasattr(o, "id"):
            continue
        pid = o.id
        lon = float(o.lon) % 360
        theta = math.radians(90 - lon)
        r = 0.75
        color = PLANET_COLORS.get(pid, "#6a1b2c")
        # тінь нижче трохи
        ax.scatter(theta + 0.01, r - 0.02, s=260, c="black", alpha=0.12, zorder=3)
        ax.scatter(theta, r, s=220, c=color, edgecolors="k", linewidths=0.6, zorder=4)
        # символ поверх
        sym = PLANET_SYMBOLS.get(pid, pid)
        # підпис (D° M' S")
        deg_label = deg_to_str_dms(lon)
        ax.text(theta, r, sym, fontsize=14, ha="center", va="center", color="white", fontweight="bold", zorder=5)
        ax.text(theta + 0.04, r + 0.03, f"{pid}\n{deg_label}", fontsize=8, ha="left", va="bottom", color=color, zorder=5)

    # 5) Ascendant та MC (якщо є) — спробуємо отримати через chart.get(const.ASC/MC) або chart.houses[0]
    asc_lon = None
    mc_lon = None
    try:
        asc_obj = chart.get(const.ASC)
        if asc_obj and hasattr(asc_obj, "lon"):
            asc_lon = float(asc_obj.lon) % 360
    except Exception:
        # fallback: take house cusp 1 as asc
        try:
            asc_lon = house_lons[0] % 360
        except Exception:
            asc_lon = None
    try:
        mc_obj = chart.get(const.MC)
        if mc_obj and hasattr(mc_obj, "lon"):
            mc_lon = float(mc_obj.lon) % 360
    except Exception:
        mc_lon = None

    if asc_lon is not None:
        theta = math.radians(90 - asc_lon)
        ax.text(theta, 0.45, "Ascendant", fontsize=9, ha="center", va="center", color="#333", fontweight="600")

    if mc_lon is not None:
        theta = math.radians(90 - mc_lon)
        ax.text(theta, 0.45, "MC", fontsize=9, ha="center", va="center", color="#333", fontweight="600")

    # 6) Лінії аспектів
    for asp in aspects_list:
        try:
            p1_id = asp["planet1"]
            p2_id = asp["planet2"]
            # знайти об'єкти в chart.objects за id
            p1 = next((x for x in chart.objects if getattr(x, "id", None) == p1_id), None)
            p2 = next((x for x in chart.objects if getattr(x, "id", None) == p2_id), None)
            if not p1 or not p2:
                continue
            a1 = math.radians(90 - float(p1.lon))
            a2 = math.radians(90 - float(p2.lon))
            # лінія по радіусу ближче до центру (експериментальна)
            r_line = 0.75
            ax.plot([a1, a2], [r_line, r_line], color=asp.get("color", "#999"), lw=1.5, alpha=0.85, zorder=2)
        except Exception:
            continue

    # 7) Логотип Albireo Daria в секторі Скорпіона (24 Oct — 22 Nov ~ 210°..-)
    try:
        # Скорпіон центр приблизно 210°
        sc_center_deg = 210
        sc_theta = math.radians(90 - sc_center_deg)
        ax.text(sc_theta, 1.25, logo_text, fontsize=12, ha="center", va="center",
                color="white", bbox=dict(facecolor="#6a1b2c", edgecolor="none", pad=4), zorder=6)
    except Exception:
        pass

    # 8) Легенди (планети та аспекти) внизу
    # Планетна легенда
    planet_handles = []
    planet_labels = []
    for pid, sym in PLANET_SYMBOLS.items():
        if pid in PLANET_COLORS:
            planet_handles.append(plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=PLANET_COLORS.get(pid,"#888"), markersize=8))
            planet_labels.append(f"{sym} {pid}")
    if planet_handles:
        try:
            leg = ax.legend(planet_handles, planet_labels, loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=4, frameon=False, fontsize=8, title="Планети")
            leg.get_title().set_color("#333")
            for t in leg.get_texts():
                t.set_color("#333")
            ax.add_artist(leg)
        except Exception:
            pass

    # Аспектна легенда
    aspect_handles = []
    aspect_labels = []
    for name, cfg in ASPECTS_DEF.items():
        aspect_handles.append(plt.Line2D([0,1],[0,0], color=cfg["color"], lw=2))
        aspect_labels.append(name.capitalize())
    if aspect_handles:
        try:
            leg2 = ax.legend(aspect_handles, aspect_labels, loc="lower center", bbox_to_anchor=(0.5, -0.24), ncol=4, frameon=False, fontsize=8, title="Аспекти")
            leg2.get_title().set_color("#333")
            for t in leg2.get_texts():
                t.set_color("#333")
            ax.add_artist(leg2)
        except Exception:
            pass

    # Save figure
    try:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)

# API: /generate
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()  # трохи захисту перед кожною генерацією

        data = request.get_json() or {}
        name = data.get("name", data.get("firstName", "Person"))
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")

        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date, time, place (і бажано name)"}), 400

        # Ключ кешу і шляхи
        key = cache_key(name, date_str, time_str, place)
        json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_cache_path = os.path.join(CACHE_DIR, f"{key}.png")

        # Якщо є і не старше 30 днів — віддаємо
        if os.path.exists(json_cache_path) and os.path.exists(png_cache_path):
            # перевіримо час останньої модифікації; якщо >30 днів — перегенеруємо
            mtime = dt.fromtimestamp(os.path.getmtime(json_cache_path))
            if dt.now() - mtime <= timedelta(days=30):
                with open(json_cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                # поправимо шляхи на URL-підхід (залишаємо стандартні шляхи)
                cached["chart_url"] = f"/cache/{key}.png"
                return jsonify(cached)

        # Геокодування
        try:
            location = geolocator.geocode(place, language="en")
        except Exception as e:
            location = None
        if not location:
            return jsonify({"error": "Місце не знайдено (геокодер)"}), 400
        lat, lon = location.latitude, location.longitude

        # timezone
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        if not tz_str:
            tz_str = "UTC"
        tz = pytz.timezone(tz_str)

        # local datetime
        try:
            naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except Exception as e:
            return jsonify({"error": f"Невірний формат дати/часу: {e}"}), 400
        local_dt = tz.localize(naive)

        # offset hours numeric (flatlib сумісність)
        offset_hours = local_dt.utcoffset().total_seconds() / 3600.0

        # prepare flatlib Datetime: flatlib accepts (YYYY/MM/DD, HH:MM, offset) in many versions
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)

        pos = GeoPos(lat, lon)

        # Chart: стара версія flatlib може використовувати параметри по-різному; прагнемо до сумісності:
        chart = None
        try:
            # new-ish API: Chart(datetime, geopos, hsys=const.HOUSES_PLACIDUS)
            chart = Chart(fdate, pos, hsys=getattr(const, "HOUSES_PLACIDUS", None) or getattr(const, "PLACIDUS", None) or "Placidus")
        except Exception:
            try:
                # fallback: Chart(fdate,pos) then set houses?
                chart = Chart(fdate, pos)
            except Exception as e:
                return jsonify({"error": f"Не вдалося створити Chart: {e}"}), 500

        # Обчислення аспектів вручну
        aspect_list = compute_aspects_manual(chart.objects)

        # Малюємо картинку (в razі відсутності файлу)
        try:
            draw_natal_chart(chart, aspect_list, png_cache_path)
        except Exception as e:
            # якщо намалювати картинку не вдалось — все одно повернемо JSON аспектів
            # логируем помилку в payload
            err_msg = f"Помилка при малюванні картинки: {e}"
            # підготуємо JSON результат, щоб не втратити розрахунки
            result = {
                "name": name,
                "date": date_str,
                "time": time_str,
                "place": place,
                "timezone": tz_str,
                "aspects_json": aspect_list,
                "chart_url": None,
                "warning": err_msg
            }
            # зберігаємо JSON кеш (щоб можна було повторно віддати)
            try:
                with open(json_cache_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return jsonify(result), 200

        # Підготовка даних для кеша/віддачі
        out = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "aspects_json": aspect_list,
            "chart_url": f"/cache/{key}.png"
        }
        # Запис JSON кеша
        try:
            with open(json_cache_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return jsonify(out)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Віддача кешованих зображень
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

# Health
@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # порт 8080 як у вас було
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))