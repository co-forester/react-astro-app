import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

# ===================== Конфіг =====================
STATIC_FOLDER = 'static'
os.makedirs(STATIC_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_FOLDER)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

# ----- Гліфи планет та знаків (Unicode) -----
PLANET_SYMBOLS = {
    const.SUN:     '☉',
    const.MOON:    '☽',
    const.MERCURY: '☿',
    const.VENUS:   '♀',
    const.MARS:    '♂',
    const.JUPITER: '♃',
    const.SATURN:  '♄',
    const.URANUS:  '♅',
    const.NEPTUNE: '♆',
    const.PLUTO:   '♇',
    # додаткові точки (малюємо як гліфи)
    const.ASC:     '↑',   # Ascendant
    const.MC:      '⚝',   # Midheaven (альт. символ)
}

ZODIAC_SIGNS = ['♈︎','♉︎','♊︎','♋︎','♌︎','♍︎','♎︎','♏︎','♐︎','♑︎','♒︎','♓︎']

# ----- Аспекти, кольори та орбіси -----
ASPECTS = {
    'conjunction': {'angle': 0,   'orb': 8, 'color': 'black'},
    'sextile':     {'angle': 60,  'orb': 5, 'color': 'green'},
    'square':      {'angle': 90,  'orb': 6, 'color': 'red'},
    'trine':       {'angle': 120, 'orb': 7, 'color': 'blue'},
    'opposition':  {'angle': 180, 'orb': 8, 'color': 'red'},
}

# ===================== Хелпери =====================
def norm_angle(a):
    a = a % 360.0
    return a if a >= 0 else a + 360.0

def ang_dist(a, b):
    d = abs(norm_angle(a) - norm_angle(b))
    return d if d <= 180 else 360 - d

def deg_to_xy(deg, r):
    """ 0° на правому боці кола, зростання проти год. стрілки (класичний вигляд).
        Екранні координати: x=cos, y=sin.
    """
    rad = math.radians(0 - deg)  # інвертуємо, щоб довкола йшло CCW з Aries праворуч
    return r * math.cos(rad), r * math.sin(rad)

def aspect_line_width(orb, max_orb):
    # товстіша лінія для точних аспектів
    return max(0.8, 2.8 - (orb / max_orb) * 2.0)

# ===================== Рендер карти =====================
def draw_natal_chart(chart, place, filename="chart.png"):
    # Параметри кола
    R_OUTER = 1.00   # зовнішнє коло (знаки)
    R_SIGNS = 0.92   # радіус підписів знаків
    R_HOUSES = 0.80  # коло домів (лінії)
    R_PLANETS = 0.74 # орбіта планет (точки)
    R_ASPECTS = 0.72 # для ліній аспектів (всередині)
    R_LOGO = 0.35    # коло логотипу

    plt.rcParams['font.family'] = 'DejaVu Sans'  # має гліфи знаків/планет
    fig, ax = plt.subplots(figsize=(8, 8), dpi=160)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis('off')

    # --- Кільця
    # Зовнішнє коло (знаки)
    outer = plt.Circle((0, 0), R_OUTER, fill=False, linewidth=2.0)
    ax.add_artist(outer)
    # Коло домів
    houses_circle = plt.Circle((0,0), R_HOUSES, fill=False, linewidth=1.2, linestyle='-')
    ax.add_artist(houses_circle)
    # Внутрішнє коло для аспектів
    inner = plt.Circle((0, 0), R_ASPECTS, fill=False, linewidth=1.0, linestyle=':')
    ax.add_artist(inner)

    # --- Знаки зодіаку (кожні 30°)
    for i, sign in enumerate(ZODIAC_SIGNS):
        start_deg = i * 30.0
        # радіальна риска на межі знаку
        x1, y1 = deg_to_xy(start_deg, R_OUTER)
        x2, y2 = deg_to_xy(start_deg, R_HOUSES + 0.02)
        ax.plot([x1, x2], [y1, y2], linewidth=1.0, color="#999999")
        # підпис знаку в центрі сектора
        mid = start_deg + 15.0
        tx, ty = deg_to_xy(mid, R_SIGNS)
        ax.text(tx, ty, sign, ha='center', va='center', fontsize=14)

        # дрібна розмітка кожні 5°
        for j in range(1, 6):
            mdeg = start_deg + j * 5
            mx1, my1 = deg_to_xy(mdeg, R_OUTER)
            mx2, my2 = deg_to_xy(mdeg, R_OUTER - (0.015 if j != 6 else 0.03))
            ax.plot([mx1, mx2], [my1, my2], linewidth=0.6, color="#CCCCCC")

    # --- Доміфікація (лінії домів)
    try:
        # 12 ліній домів за плоскидом (за замовчуванням у flatlib Chart)
        house_lines = []
        for h in range(1, 13):
            cusp = chart.houses.get(h).lon  # градуси екліптики
            xh1, yh1 = deg_to_xy(cusp, R_HOUSES)
            xh2, yh2 = deg_to_xy(cusp, R_OUTER)
            ax.plot([xh1, xh2], [yh1, yh2], linewidth=1.0, color="#666666")
            house_lines.append(cusp)

        # підписи номерів домів ближче до центру
        for h in range(1, 13):
            mid = norm_angle((house_lines[h-1] + house_lines[h-2]) / 2.0) if h > 1 else \
                  norm_angle((house_lines[h-1] + house_lines[11]) / 2.0)
            tx, ty = deg_to_xy(mid, R_HOUSES - 0.05)
            ax.text(tx, ty, str(h), ha='center', va='center', fontsize=10, color="#666666")
    except Exception:
        # без домів — ок, не валимо рендер
        pass

    # --- Позиції планет + ASC/MC
    objects = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
        const.ASC, const.MC
    ]

    planet_positions = {}  # id -> lon
    for obj in objects:
        try:
            body = chart.get(obj)
            lon = float(body.lon)
            planet_positions[obj] = lon
        except Exception:
            continue

    # --- Планети (точки + гліфи)
    for obj, lon in planet_positions.items():
        x, y = deg_to_xy(lon, R_PLANETS)
        ax.plot(x, y, marker='o', markersize=8, color="#222222")
        glyph = PLANET_SYMBOLS.get(obj, '?')
        ax.text(x, y, glyph, ha='center', va='center', fontsize=13, color="#111111")

    # --- Аспекти (між планетами; ASC/MC не з’єднуємо)
    planet_only = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
                   const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]
    for i in range(len(planet_only)):
        a_id = planet_only[i]
        if a_id not in planet_positions:
            continue
        a_lon = planet_positions[a_id]
        ax_a, ay_a = deg_to_xy(a_lon, R_ASPECTS)
        for j in range(i + 1, len(planet_only)):
            b_id = planet_only[j]
            if b_id not in planet_positions:
                continue
            b_lon = planet_positions[b_id]
            d = ang_dist(a_lon, b_lon)
            # шукаємо, чи вкладається у будь-який аспект з орбісом
            for asp_name, props in ASPECTS.items():
                angle = props['angle']
                orb = props['orb']
                delta = abs(d - angle)
                if delta <= orb:
                    # чим точніший аспект, тим товща лінія
                    lw = aspect_line_width(delta, orb)
                    color = props['color']
                    ax_b, ay_b = deg_to_xy(b_lon, R_ASPECTS)
                    ax.plot([ax_a, ax_b], [ay_a, ay_b], color=color, linewidth=lw, alpha=0.9)
                    break  # один аспект на пару

    # --- Легенда справа (планети + довготи)
    try:
        legend_items = []
        for obj in planet_only:
            if obj in planet_positions:
                glyph = PLANET_SYMBOLS.get(obj, '?')
                val = planet_positions[obj]
                sign_ix = int(norm_angle(val) // 30)
                deg_in_sign = norm_angle(val) % 30
                legend_items.append(f"{glyph}  {deg_in_sign:05.2f}°  {ZODIAC_SIGNS[sign_ix]}")
        # Вивід легенди у текстовому блоці
        if legend_items:
            txt = "\n".join(legend_items)
            ax.text(1.12, 0.0, txt, transform=ax.transData,
                    fontsize=10, va='center', ha='left', color="#222222")
    except Exception:
        pass

    # --- Заголовок + підпис місця
    ax.text(0, 1.06, f"Натальна карта — {place}", ha='center', va='center',
            fontsize=14, fontweight='bold')

    # --- Логотип усередині
    ax.text(0, -R_LOGO, "Albireo Daria", ha='center', va='center',
            fontsize=12, color="#444444", style='italic')

    # Збереження
    out_path = os.path.join(STATIC_FOLDER, filename)
    fig.savefig(out_path, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    return out_path

# ===================== Flask routes =====================
@app.route('/')
def index():
    return "🔮 Astro API працює! Використовуйте /generate для побудови натальної карти."

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json or {}
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not (date and time and place):
        return jsonify({
            'chart_image_url': None,
            'status': 'error',
            'error': 'Введіть дату, час та місце'
        }), 400

    chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
    status = "ok"
    error_msg = None

    try:
        # Геокодування
        location = geolocator.geocode(place, timeout=10)
        if not location:
            raise ValueError(f"Місто '{place}' не знайдено")

        lat, lon = location.latitude, location.longitude

        # Часовий пояс
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        tz = pytz.timezone(tz_name)

        # Локальна дата/час -> UTC для flatlib
        dt_local = tz.localize(dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
        dt_utc = dt_local.astimezone(pytz.utc)
        fdate = dt_utc.strftime("%Y/%m/%d")
        ftime = dt_utc.strftime("%H:%M")

        geopos = GeoPos(str(lat), str(lon))
        fdt = Datetime(fdate, ftime, "+00:00")

        # Створюємо карту (Placidus за замовчуванням)
        chart = Chart(fdt, geopos)

        # Малюємо профі карту
        draw_natal_chart(chart, place, filename="chart.png")

    except Exception as e:
        # fallback картинка, щоб фронт завжди мав що показати
        status = "stub"
        error_msg = str(e)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.axis('off')
        ax.text(0.5, 0.55, "Натальна карта (заглушка)", ha='center', va='center', fontsize=14)
        ax.text(0.5, 0.45, place, ha='center', va='center', fontsize=11, color="#666666")
        fig.savefig(chart_path, bbox_inches='tight', pad_inches=0.2)
        plt.close(fig)

    return jsonify({
        "chart_image_url": "/static/chart.png",
        "status": status,
        "error": error_msg
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)