import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory, Response
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
    # додаткові точки
    const.ASC:     '↑',
    const.MC:      '⚝',
}
ZODIAC_SIGNS = ['♈︎','♉︎','♊︎','♋︎','♌︎','♍︎','♎︎','♏︎','♐︎','♑︎','♒︎','♓︎']

# ----- Аспекти, кольори та орбіси -----
ASPECTS = {
    'conjunction': {'ua': 'З’єднання', 'angle': 0,   'orb': 8, 'color': 'black'},
    'sextile':     {'ua': 'Секстиль',  'angle': 60,  'orb': 5, 'color': 'green'},
    'square':      {'ua': 'Квадрат',   'angle': 90,  'orb': 6, 'color': 'red'},
    'trine':       {'ua': 'Тригон',    'angle': 120, 'orb': 7, 'color': 'blue'},
    'opposition':  {'ua': 'Опозиція',  'angle': 180, 'orb': 8, 'color': 'red'},
}

# ===================== Хелпери =====================
def norm_angle(a):
    a = a % 360.0
    return a if a >= 0 else a + 360.0

def ang_dist(a, b):
    d = abs(norm_angle(a) - norm_angle(b))
    return d if d <= 180 else 360 - d

def deg_to_xy(deg, r):
    rad = math.radians(0 - deg)  # Aries праворуч, оберт CCW
    return r * math.cos(rad), r * math.sin(rad)

def aspect_line_width(orb, max_orb):
    return max(0.8, 2.8 - (orb / max_orb) * 2.0)

def deg_to_sign_pos(lon):
    lon = norm_angle(lon)
    sign_ix = int(lon // 30)
    deg_in_sign = lon % 30
    d = int(deg_in_sign)
    m = int(round((deg_in_sign - d) * 60))
    if m == 60:
        d += 1
        m = 0
    return ZODIAC_SIGNS[sign_ix], d, m

# ===================== Рендер карти =====================
def draw_natal_chart(chart, place, filename="chart.png"):
    R_OUTER = 1.00
    R_SIGNS = 0.92
    R_HOUSES = 0.80
    R_PLANETS = 0.74
    R_ASPECTS = 0.72
    R_LOGO = 0.35

    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(8, 8), dpi=160)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis('off')

    outer = plt.Circle((0, 0), R_OUTER, fill=False, linewidth=2.0)
    ax.add_artist(outer)
    houses_circle = plt.Circle((0,0), R_HOUSES, fill=False, linewidth=1.2, linestyle='-')
    ax.add_artist(houses_circle)
    inner = plt.Circle((0, 0), R_ASPECTS, fill=False, linewidth=1.0, linestyle=':')
    ax.add_artist(inner)

    # Знаки та розмітка
    for i, sign in enumerate(ZODIAC_SIGNS):
        start_deg = i * 30.0
        x1, y1 = deg_to_xy(start_deg, R_OUTER)
        x2, y2 = deg_to_xy(start_deg, R_HOUSES + 0.02)
        ax.plot([x1, x2], [y1, y2], linewidth=1.0, color="#999999")
        mid = start_deg + 15.0
        tx, ty = deg_to_xy(mid, R_SIGNS)
        ax.text(tx, ty, sign, ha='center', va='center', fontsize=14)
        for j in range(1, 6):
            mdeg = start_deg + j * 5
            mx1, my1 = deg_to_xy(mdeg, R_OUTER)
            mx2, my2 = deg_to_xy(mdeg, R_OUTER - (0.015 if j != 6 else 0.03))
            ax.plot([mx1, mx2], [my1, my2], linewidth=0.6, color="#CCCCCC")

    # Доміфікація
    try:
        house_lons = []
        for h in range(1, 13):
            cusp = chart.houses.get(h).lon
            xh1, yh1 = deg_to_xy(cusp, R_HOUSES)
            xh2, yh2 = deg_to_xy(cusp, R_OUTER)
            ax.plot([xh1, xh2], [yh1, yh2], linewidth=1.0, color="#666666")
            house_lons.append(cusp)
        for h in range(1, 13):
            mid = norm_angle((house_lons[h-1] + house_lons[h-2]) / 2.0) if h > 1 else \
                  norm_angle((house_lons[h-1] + house_lons[11]) / 2.0)
            tx, ty = deg_to_xy(mid, R_HOUSES - 0.05)
            ax.text(tx, ty, str(h), ha='center', va='center', fontsize=10, color="#666666")
    except Exception:
        pass

    # Позиції планет
    objects = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
        const.ASC, const.MC
    ]
    planet_positions = {}
    for obj in objects:
        try:
            body = chart.get(obj)
            lon = float(body.lon)
            planet_positions[obj] = lon
        except Exception:
            continue

    # Планети точки+гліфи
    for obj, lon in planet_positions.items():
        x, y = deg_to_xy(lon, R_PLANETS)
        ax.plot(x, y, marker='o', markersize=8, color="#222222")
        glyph = PLANET_SYMBOLS.get(obj, '?')
        ax.text(x, y, glyph, ha='center', va='center', fontsize=13, color="#111111")

    # Аспекти (між планетами, без ASC/MC)
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
            for asp_name, props in ASPECTS.items():
                angle = props['angle']
                orb = props['orb']
                delta = abs(d - angle)
                if delta <= orb:
                    lw = aspect_line_width(delta, orb)
                    color = props['color']
                    ax_b, ay_b = deg_to_xy(b_lon, R_ASPECTS)
                    ax.plot([ax_a, ax_b], [ay_a, ay_b], color=color, linewidth=lw, alpha=0.9)
                    break

    # Легенда праворуч
    try:
        legend_items = []
        for obj in planet_only:
            if obj in planet_positions:
                glyph = PLANET_SYMBOLS.get(obj, '?')
                val = planet_positions[obj]
                sign_ix = int(norm_angle(val) // 30)
                deg_in_sign = norm_angle(val) % 30
                legend_items.append(f"{glyph}  {deg_in_sign:05.2f}°  {ZODIAC_SIGNS[sign_ix]}")
        if legend_items:
            txt = "\n".join(legend_items)
            ax.text(1.12, 0.0, txt, transform=ax.transData,
                    fontsize=10, va='center', ha='left', color="#222222")
    except Exception:
        pass

    ax.text(0, 1.06, f"Натальна карта — {place}", ha='center', va='center',
            fontsize=14, fontweight='bold')
    ax.text(0, -R_LOGO, "Albireo Daria", ha='center', va='center',
            fontsize=12, color="#444444", style='italic')

    out_path = os.path.join(STATIC_FOLDER, filename)
    fig.savefig(out_path, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    return out_path

def compute_aspects(planet_positions):
    """Повертає список аспектів між класичними планетами."""
    planet_only = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
    ]
    out = []
    for i in range(len(planet_only)):
        a = planet_only[i]
        if a not in planet_positions:
            continue
        for j in range(i+1, len(planet_only)):
            b = planet_only[j]
            if b not in planet_positions:
                continue
            a_lon = planet_positions[a]
            b_lon = planet_positions[b]
            d = ang_dist(a_lon, b_lon)
            for key, props in ASPECTS.items():
                angle = props['angle']
                orb = props['orb']
                delta = abs(d - angle)
                if delta <= orb:
                    out.append({
                        "a": a, "b": b,
                        "a_lon": a_lon, "b_lon": b_lon,
                        "type": key,
                        "type_ua": props['ua'],
                        "angle": angle,
                        "distance": round(d, 2),
                        "orb": round(delta, 2),
                    })
                    break
    # Сортуємо за точністю (менший орб — вище)
    out.sort(key=lambda x: x["orb"])
    return out

def html_aspect_table(aspects):
    """Рендер HTML-таблиці аспектів."""
    if not aspects:
        return "<p style='margin:0.5rem 0;color:#666'>Аспектів не виявлено в заданих орбісах.</p>"

    def pname(pid):
        return PLANET_SYMBOLS.get(pid, '?')

    rows = []
    for asp in aspects:
        sign_a, da, ma = deg_to_sign_pos(asp["a_lon"])
        sign_b, db, mb = deg_to_sign_pos(asp["b_lon"])
        rows.append(f"""
        <tr>
          <td>{pname(asp["a"])}</td>
          <td>{da:02d}°{ma:02d}′ {sign_a}</td>
          <td>{asp["type_ua"]}</td>
          <td>{pname(asp["b"])}</td>
          <td>{db:02d}°{mb:02d}′ {sign_b}</td>
          <td>{asp["distance"]}°</td>
          <td>{asp["orb"]}°</td>
        </tr>
        """)

    table = f"""
    <table class="aspects">
      <thead>
        <tr>
          <th>Планета A</th>
          <th>Позиція A</th>
          <th>Аспект</th>
          <th>Планета B</th>
          <th>Позиція B</th>
          <th>Кут</th>
          <th>Орб</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    """
    return table

def build_html_page(place, ts_param, aspect_table_html):
    """Повна HTML-сторінка з картою та таблицею аспектів."""
    return f"""<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Натальна карта — {place}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "DejaVu Sans", Arial, sans-serif;
      margin: 0; padding: 1rem; color: #111; background: #fff;
    }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    .title {{ font-size: 1.25rem; font-weight: 700; margin: 0 0 0.75rem; }}
    .chart {{
      display: block; width: 100%; max-width: 720px; margin: 0 auto 1rem; border-radius: 12px;
      box-shadow: 0 6px 24px rgba(0,0,0,.08);
    }}
    .section-title {{
      font-size: 1.05rem; font-weight: 600; margin: 1rem 0 .5rem; color: #333;
    }}
    .aspects {{
      width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 12px;
      box-shadow: 0 6px 24px rgba(0,0,0,.06);
    }}
    .aspects th, .aspects td {{ padding: .6rem .7rem; border-bottom: 1px solid #eee; text-align: left; }}
    .aspects thead th {{ background: #fafafa; font-weight: 700; font-size: .9rem; }}
    .aspects tbody tr:hover {{ background: #fcfcfc; }}
    .muted {{ color: #666; font-size: .9rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1 class="title">Натальна карта — {place}</h1>
    <img class="chart" src="/static/chart.png?ts={ts_param}" alt="Натальна карта {place}" />
    <div class="section-title">Таблиця аспектів</div>
    {aspect_table_html}
    <p class="muted">Згенеровано сервісом Albireo Daria.</p>
  </div>
</body>
</html>
"""

# ===================== Flask routes =====================
@app.route('/')
def index():
    return "🔮 Astro API працює! Використовуйте /generate для побудови натальної карти."

@app.route('/generate', methods=['POST'])
def generate():
    """Старий JSON-ендпоінт — не чіпаємо (зворотна сумісність)."""
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
        location = geolocator.geocode(place, timeout=10)
        if not location:
            raise ValueError(f"Місто '{place}' не знайдено")
        lat, lon = location.latitude, location.longitude

        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        tz = pytz.timezone(tz_name)

        dt_local = tz.localize(dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
        dt_utc = dt_local.astimezone(pytz.utc)
        fdate = dt_utc.strftime("%Y/%m/%d")
        ftime = dt_utc.strftime("%H:%M")

        geopos = GeoPos(float(lat), float(lon))
        fdt = Datetime(fdate, ftime, "+00:00")

        chart = Chart(fdt, geopos)
        draw_natal_chart(chart, place, filename="chart.png")

    except Exception as e:
        status = "stub"
        error_msg = str(e)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.axis('off')
        ax.text(0.5, 0.55, "Натальна карта (заглушка)", ha='center', va='center', fontsize=14)
        ax.text(0.5, 0.45, place or "", ha='center', va='center', fontsize=11, color="#666666")
        fig.savefig(chart_path, bbox_inches='tight', pad_inches=0.2)
        plt.close(fig)

    return jsonify({
        "chart_image_url": "/static/chart.png",
        "status": status,
        "error": error_msg
    })

@app.route('/generate_html', methods=['POST'])
def generate_html():
    """Новий ендпоінт: повертає готову HTML-сторінку з картою та таблицею аспектів."""
    data = request.json or {}
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    if not (date and time and place):
        return Response("<p>Помилка: введіть дату, час і місце.</p>", mimetype="text/html", status=400)

    chart_path = os.path.join(STATIC_FOLDER, 'chart.png')
    try:
        location = geolocator.geocode(place, timeout=10)
        if not location:
            raise ValueError(f"Місто '{place}' не знайдено")
        lat, lon = location.latitude, location.longitude

        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        tz = pytz.timezone(tz_name)

        dt_local = tz.localize(dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"))
        dt_utc = dt_local.astimezone(pytz.utc)
        fdate = dt_utc.strftime("%Y/%m/%d")
        ftime = dt_utc.strftime("%H:%M")

        geopos = GeoPos(float(lat), float(lon))
        fdt = Datetime(fdate, ftime, "+00:00")

        chart = Chart(fdt, geopos)
        # Малюємо карту
        draw_natal_chart(chart, place, filename="chart.png")

        # Збираємо позиції планет для аспектів
        planet_positions = {}
        for pid in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
                    const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]:
            try:
                planet_positions[pid] = float(chart.get(pid).lon)
            except Exception:
                pass

        aspects = compute_aspects(planet_positions)
        aspect_table = html_aspect_table(aspects)
        html = build_html_page(place, ts_param=int(dt.utcnow().timestamp()), aspect_table_html=aspect_table)
        return Response(html, mimetype="text/html")

    except Exception as e:
        # fallback HTML з заглушкою
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.axis('off')
        ax.text(0.5, 0.55, "Натальна карта (заглушка)", ha='center', va='center', fontsize=14)
        ax.text(0.5, 0.45, place or "", ha='center', va='center', fontsize=11, color="#666666")
        fig.savefig(chart_path, bbox_inches='tight', pad_inches=0.2)
        plt.close(fig)
        fallback_html = f"""<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><title>Помилка</title></head>
<body style="font-family:Arial,sans-serif;padding:1rem">
  <h1 style="margin:.2rem 0 1rem">Натальна карта — {place}</h1>
  <img src="/static/chart.png" style="max-width:720px;width:100%;border-radius:12px" />
  <p style="color:#b00020">Помилка: {str(e)}</p>
</body></html>"""
        return Response(fallback_html, mimetype="text/html", status=200)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)