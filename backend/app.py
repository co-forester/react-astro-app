# app.py — професійна натальна карта (Placidus), кеш PNG/JSON,
# дугові підписи, логотип по дузі (♏), DMS, ASC/MC/IC/DSC, хорди аспектів, таблиця аспектів

import os
import json
import hashlib
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt

from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects

app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
    "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "North Node": "☊", "South Node": "☋", "Pars Fortuna": "⚶"
}

ASPECT_COLORS = {
    "conjunction": "#FF0000",
    "opposition": "#0000FF",
    "trine": "#00FF00",
    "square": "#FFA500",
    "sextile": "#1F77B4"
}

def draw_chart(chart, filename):
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.2,1.2)
    ax.set_ylim(-1.2,1.2)
    ax.axis('off')

    # Зодіак (полярність)
    for i in range(12):
        start = 2*math.pi*(i/12)
        end = 2*math.pi*((i+1)/12)
        ax.plot([0, math.cos(start)], [0, math.sin(start)], color="grey", lw=1)

    # Планети
    planets_list = []
    for p in chart.objects:
        if p.isPlanet():
            angle = math.radians(p.lon)
            x, y = math.cos(angle), math.sin(angle)
            ax.text(x*1.05, y*1.05, PLANET_SYMBOLS.get(p.id, p.id), fontsize=12, ha='center', va='center')
            planets_list.append({
                "name": p.id,
                "symbol": PLANET_SYMBOLS.get(p.id, p.id),
                "lon": p.lon
            })

    # Аспекти прямими хордами
    aspect_lines = []
    for asp in aspects.find(chart):
        if asp.type in ASPECT_COLORS:
            p1 = next(o for o in chart.objects if o.id==asp.obj1)
            p2 = next(o for o in chart.objects if o.id==asp.obj2)
            x1, y1 = math.cos(math.radians(p1.lon)), math.sin(math.radians(p1.lon))
            x2, y2 = math.cos(math.radians(p2.lon)), math.sin(math.radians(p2.lon))
            ax.plot([x1, x2], [y1, y2], color=ASPECT_COLORS[asp.type], lw=1)
            aspect_lines.append({
                "planet1": p1.id,
                "planet1_symbol": PLANET_SYMBOLS.get(p1.id, p1.id),
                "planet2": p2.id,
                "planet2_symbol": PLANET_SYMBOLS.get(p2.id, p2.id),
                "type": asp.type,
                "angle_dms": f"{int(asp.angle)}°"
            })

    fig.savefig(filename, bbox_inches='tight')
    plt.close(fig)
    return planets_list, aspect_lines

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

        # перевірка кеша
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
            # повертаємо помилку у форматі, схожому на твою робочу версію
            return jsonify({"error": "Exception", "message": str(e)}), 400

        fdate = Datetime(local_dt.strftime("%Y/%m/%d"), local_dt.strftime("%H:%M"), offset_hours)
        pos = GeoPos(lat, lon)
        try:
            chart = Chart(fdate, pos, hsys='P')
        except Exception:
            chart = Chart(fdate, pos)

        # аспекти (зручний JSON список)
        aspects_json = compute_aspects_manual(chart.objects)

        # малюємо картку (в draw використовуємо aspects_json)
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