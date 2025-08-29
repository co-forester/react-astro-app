# app.py — робоча версія з поясненнями, обробкою помилок та "try" блоками
import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — безголовий режим для контейнера
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# ----------------------------------------
# Ініціалізація глобальних об'єктів
# ----------------------------------------
geolocator = Nominatim(user_agent="my_astrology_app")
tf = TimezoneFinder()

app = Flask(__name__)
CORS(app)

# Папка для кешу (json + png)
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ----------------------------------------
# Конфіг/параметри: символи, кольори, аспекти
# ----------------------------------------
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

# Визначення аспектів: (кут, колір, орб)
ASPECTS_DEF = {
    "conjunction": {"angle": 0, "orb": 8, "color": "#cccccc"},
    "sextile": {"angle": 60, "orb": 6, "color": "#f7eaea"},
    "square": {"angle": 90, "orb": 6, "color": "#f59ca9"},
    "trine": {"angle": 120, "orb": 8, "color": "#d4a5a5"},
    "opposition": {"angle": 180, "orb": 8, "color": "#4a0f1f"},
}

# ----------------------------------------
# Утиліти
# ----------------------------------------
def cleanup_cache(days: int = 30):
    """Видаляє файли в CACHE_DIR старші ніж days днів."""
    now_ts = dt.now().timestamp()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        try:
            if os.path.isfile(fpath):
                if now_ts - os.path.getmtime(fpath) > days * 24 * 3600:
                    os.remove(fpath)
        except Exception:
            # не губимося якщо файл зайнятий/вже видалено
            pass

def cache_key(name, date_str, time_str, place):
    """Генерує MD5-хеш для кешування результатів запиту."""
    raw = f"{name}_{date_str}_{time_str}_{place}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def deg_to_dms(angle):
    """Конвертація десяткових градусів у рядок D°M'S\""""
    d = int(angle)
    m = int((angle - d) * 60)
    s = int(((angle - d) * 60 - m) * 60)
    return f"{d}°{m}'{s}\""

# ----------------------------------------
# Обчислення аспектів (ручний, по довготам)
# ----------------------------------------
def compute_aspects_manual(objects):
    """
    Приймає список об'єктів (chart.objects) — обчислює аспекти між тими, що в PLANET_SYMBOLS.
    Повертає список словників з planet1, planet2, type, angle (десятковий), color.
    """
    results = []
    objs = [o for o in objects if getattr(o, "id", None) in PLANET_SYMBOLS]
    for i in range(len(objs)):
        for j in range(i+1, len(objs)):
            p1 = objs[i]; p2 = objs[j]
            # довгота планет (0-360)
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
                        "angle_dms": deg_to_dms(round(diff, 2)),
                        "color": cfg["color"]
                    })
                    break
    return results

# ----------------------------------------
# Малювання натальної карти (сектори, градуйровка, підписи, логотип-дуга)
# ----------------------------------------
def draw_natal_chart(chart, aspects_list, save_path, logo_text="Albireo Daria ♏"):
    """
    Малює натальну карту з:
    - будинками у пастельних секторах (Placidus),
    - градуюванням по колу,
    - символами планет та аспектами,
    - бордовими дугами знаків зодіаку з білими символами/назвами,
    - логотипом білим по дузі у Скорпіоні,
    - центральним бордовим колом з ім’ям.
    """
    try:
        figsize = (12, 12)
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111, polar=True)
        ax.set_theta_direction(-1)
        ax.set_theta_offset(math.pi/2)
        ax.set_ylim(0, 1.4)
        ax.set_xticks([]); ax.set_yticks([])
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        unicode_font = "DejaVu Sans"
        plt.rcParams["font.family"] = unicode_font

        # --- Пастельні будинки ---
        house_colors = [
            "#ffe5e5", "#fff0cc", "#e6ffe6", "#e6f0ff", "#f9e6ff", "#e6ffff",
            "#fff5e6", "#f0f0f0", "#ffe6f0", "#e6ffe6", "#e6f0ff", "#fff0e6"
        ]
        try:
            for i in range(12):
                start_deg = chart.houses[i].lon % 360
                end_deg = chart.houses[(i+1) % 12].lon % 360
                if end_deg <= start_deg:
                    end_deg += 360
                theta_start = math.radians(90 - start_deg)
                theta_end = math.radians(90 - end_deg)
                width = abs(theta_end - theta_start)
                ax.bar(
                    x=(theta_start + theta_end) / 2,
                    height=1.4, width=width, bottom=0,
                    color=house_colors[i % len(house_colors)],
                    edgecolor="white", linewidth=0.5, alpha=0.35, zorder=0
                )
        except Exception as e:
            print("House draw error:", e)

        # --- Бордові дуги для знаків ---
        zodiac_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
        zodiac_names = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                        "Стрілець","Козеріг","Водолій","Риби"]
        for i, sym in enumerate(zodiac_symbols):
            start_deg = i * 30
            end_deg = start_deg + 30
            theta_start = math.radians(90 - start_deg)
            theta_end = math.radians(90 - end_deg)
            width = abs(theta_end - theta_start)

            # бордова дуга
            ax.bar(
                x=(theta_start + theta_end) / 2,
                height=1.32, width=width, bottom=1.18,
                color="#6a1b2c", edgecolor="white", linewidth=1.2, zorder=1
            )

            # символ + назва
            center_deg = start_deg + 15
            theta = math.radians(90 - center_deg)
            ax.text(theta, 1.25, sym, fontsize=20, ha="center", va="center",
                    color="white", fontfamily=unicode_font, fontweight="bold", zorder=2)
            ax.text(theta, 1.34, zodiac_names[i], fontsize=9, ha="center", va="center",
                    color="white", fontfamily=unicode_font, zorder=2)

        # --- Логотип у секторі Скорпіона ---
        try:
            scorpio_deg = 210
            theta = math.radians(90 - scorpio_deg)
            ax.text(theta, 1.28, logo_text, fontsize=12, ha="center", va="center",
                    color="white", fontfamily=unicode_font, fontweight="bold", zorder=3,
                    rotation=0)
        except Exception:
            pass

        # --- Центральне бордове коло з ім'ям ---
        try:
            circle = plt.Circle((0,0), 0.2, color="#6a1b2c", zorder=10)
            ax.add_artist(circle)
            ax.text(0, 0, chart.date.date, fontsize=12, ha="center", va="center",
                    color="white", fontfamily=unicode_font, fontweight="bold")
        except Exception:
            pass

        # --- Градуйровка ---
        for deg in range(0, 360, 30):
            theta = math.radians(90 - deg)
            ax.text(theta, 1.15, str(deg), fontsize=8, ha="center", va="center", color="black")
        # >>> Додано: малювання домів по Пласідусу
       
        houses = chart.houses

        # Пастельні кольори секторів (12 тонів)
   # >>> Правильне малювання будинків по Пласідусу
        house_colors = [
            "#fde0dc", "#f8bbd0", "#e1bee7", "#d1c4e9",
            "#c5cae9", "#bbdefb", "#b3e5fc", "#b2ebf2",
            "#b2dfdb", "#c8e6c9", "#dcedc8", "#f0f4c3"
        ]

        for i in range(1, 13):  # House numbers 1..12
            house1 = chart.houses.get(i)          # куспід дому i
            house2 = chart.houses.get(i % 12 + 1)  # куспід наступного дому
            if not (house1 and house2):
                continue

            cusp1 = house1.lon
            cusp2 = house2.lon
            theta1, theta2 = math.radians(90 - cusp1), math.radians(90 - cusp2)

            wedge = plt.matplotlib.patches.Wedge(
                center=(0, 0), r=1.0,
                theta1=math.degrees(theta2),
                theta2=math.degrees(theta1),
                facecolor=house_colors[i-1],
                alpha=0.3,
                edgecolor="white",
                linewidth=1.0
            )
            ax.add_patch(wedge)

            mid_angle = (cusp1 + ((cusp2 - cusp1) % 360) / 2) % 360
            x_text = 0.75 * math.cos(math.radians(90 - mid_angle))
            y_text = 0.75 * math.sin(math.radians(90 - mid_angle))
            ax.text(x_text, y_text, str(i), ha="center", va="center",
                    fontsize=10, color="black", weight="bold")
                    
        # --- Планети ---
        for obj in chart.objects:
            try:
                oid = getattr(obj, "id", None)
                if oid in PLANET_SYMBOLS:
                    angle_deg = obj.lon % 360
                    theta = math.radians(90 - angle_deg)
                    r = 0.9
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

        # Логотип на бордовій дузі поруч зі знаком Скорпіона (підгон за градусом)
        try:
            # Центр приблизно на 210° як раніше — приведемо до системи 0..360 для зручності
            sc_center_deg = 210
            sc_theta = math.radians(90 - sc_center_deg)
            ax.text(sc_theta, 1.27, logo_text, fontsize=14, ha="center", va="center",
                    color="white", fontfamily=unicode_font, fontweight="bold",
                    bbox=dict(facecolor="#6a1b2c", edgecolor="none", pad=5, boxstyle="round,pad=0.4"), zorder=6)
        except Exception:
            pass

        # Збереження з захистом
        try:
            plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        finally:
            plt.close(fig)

    except Exception as e:
        # Лог помилки у консоль — допоможе у логах gunicorn/fly
        print("Error in draw_natal_chart:", e)
        traceback.print_exc()
        # і піднімемо виключення далі, щоб виклик виконав обробку
        raise

# ----------------------------------------
# Маршрут: /generate
# ----------------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Почистити кеш (не обов'язково щохвилини)
        cleanup_cache()

        data = request.get_json() or {}
        name = data.get("name", data.get("firstName", "Person"))
        date_str = data.get("date")    # очікуємо формат YYYY-MM-DD
        time_str = data.get("time")    # очікуємо формат HH:MM (24h)
        place = data.get("place")

        if not (date_str and time_str and place):
            return jsonify({"error": "Надішліть date (YYYY-MM-DD), time (HH:MM) та place (рядок)"}), 400

        # Підготовка кеш-шляхів
        key = cache_key(name, date_str, time_str, place)
        json_cache_path = os.path.join(CACHE_DIR, f"{key}.json")
        png_cache_path = os.path.join(CACHE_DIR, f"{key}.png")

        # Якщо в кеші — повертати
        if os.path.exists(json_cache_path) and os.path.exists(png_cache_path):
            try:
                mtime = dt.fromtimestamp(os.path.getmtime(json_cache_path))
                if dt.now() - mtime <= timedelta(days=30):
                    with open(json_cache_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    base_url = request.host_url.rstrip("/")
                    cached["chart_url"] = f"{base_url}/cache/{key}.png"
                    return jsonify(cached)
            except Exception:
                # Якщо кеш пошкоджений — продовжимо робити заново
                pass

        # Геокодування: place -> lat, lon
        try:
            location = geolocator.geocode(place, language="en")
            if not location:
                return jsonify({"error": "Місце не знайдено (геокодер)"}), 400
            lat, lon = location.latitude, location.longitude
        except Exception as e:
            return jsonify({"error": f"Помилка геокодування: {str(e)}"}), 500

        # Знайти часовий пояс за координатами
        try:
            tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            tz = pytz.timezone(tz_str)
        except Exception:
            tz_str = "UTC"
            tz = pytz.timezone("UTC")

        # Парсимо local datetime
        try:
            naive = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            local_dt = tz.localize(naive)
            offset_hours = local_dt.utcoffset().total_seconds() / 3600.0
        except Exception as e:
            return jsonify({"error": f"Невірний формат date/time: {str(e)}"}), 400

        # Побудова Chart (flatlib)
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        try:
            chart = Chart(fdate, pos, hsys=getattr(const, "HOUSES_PLACIDUS", None) or "Placidus")
        except Exception:
            chart = Chart(fdate, pos)

        # Обчислення аспектів (вручну)
        aspect_list = compute_aspects_manual(chart.objects)

        # Малюємо та зберігаємо картинку
        try:
            draw_natal_chart(chart, aspect_list, png_cache_path)
        except Exception as e:
            # Якщо картинка не згенерувалась — все одно повернемо JSON з warning
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
            "name": name, "date": date_str, "time": time_str,
            "place": place, "timezone": tz_str,
            "aspects_json": aspect_list,
            "chart_url": f"{base_url}/cache/{key}.png"
        }
        with open(json_cache_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        return jsonify(out)

    except Exception as e:
        # Загальний catch — логування і відправка помилки
        print("Unhandled error in /generate:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Файловий ендпоінт для картинок
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Для деплоя на fly.io ми використовуємо PORT з оточення (або 8080 локально)
    port = int(os.environ.get("PORT", 8080))
    # debug=False у production; при локальному тесті можна ставити True
    app.run(host="0.0.0.0", port=port, debug=False)