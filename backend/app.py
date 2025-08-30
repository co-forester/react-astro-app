import os
import math
from datetime import datetime as dt

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
from flatlib import aspects, const

# --- Налаштування Flask ---
app = Flask(__name__)
CORS(app)

CHART_FILE = 'chart.png'

# --- Функції ---
def get_coordinates(place_name):
    geolocator = Nominatim(user_agent="astro_app")
    try:
        location = geolocator.geocode(place_name, timeout=10)
        if not location:
            return None, None
        return location.latitude, location.longitude
    except Exception as e:
        print(f"Помилка геокодування: {e}")
        return None, None

def get_timezone(lat, lon):
    try:
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        if tz_str:
            return pytz.timezone(tz_str)
    except Exception as e:
        print(f"Помилка визначення таймзони: {e}")
    return pytz.utc

def parse_datetime(date_str, time_str, tzinfo):
    dt_str = f"{date_str} {time_str}"
    naive_dt = dt.strptime(dt_str, "%Y-%m-%d %H:%M")
    return tzinfo.localize(naive_dt)

def deg_to_dms(angle):
    d = int(angle)
    m = int((angle - d) * 60)
    s = round((angle - d - m/60)*3600,2)
    return f"{d}°{m}'{s}\""

def generate_chart(chart, name):
    plt.figure(figsize=(10,10))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_zero_location('S')
    ax.set_theta_direction(-1)

    # Зодіакальні кольорові сектори 12 домів
    sign_names = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                  "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    for i in range(12):
        start = math.radians(i*30)
        ax.barh(1.5, math.radians(30), left=start, height=1.0,
                color=plt.cm.tab20(i*2), edgecolor='k', alpha=0.3)
        # Підписи знаків зодіаку
        angle = start + math.radians(15)
        ax.text(angle, 1.7, sign_names[i], ha='center', va='center',
                fontsize=10, rotation=-(i*30+15), rotation_mode='anchor')

    # Логотип/ім'я в центрі
    ax.text(0,0,name,ha='center',va='center', fontsize=16, fontweight='bold')

    # Планети
    for obj in chart.objects:
        if obj.type in const.PLANETS:
            lon = math.radians(obj.lon)
            ax.plot(lon, 2.5, 'o', markersize=10, label=obj.id)
            ax.text(lon, 2.6, f"{obj.id}\n{deg_to_dms(obj.lon)}",
                    ha='center', va='bottom', fontsize=8)

    # Аспекти
    for asp in aspects.find(chart, const.CONJUNCTION, const.SEXTILE, const.SQUARE,
                            const.TRINE, const.OPPOSITION):
        lon1 = math.radians(asp.obj1.lon)
        lon2 = math.radians(asp.obj2.lon)
        ax.plot([lon1, lon2], [2.5,2.5], 'r-', alpha=0.5)

    ax.set_ylim(0,3)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()
    return CHART_FILE

def get_aspects_json(chart):
    result = []
    for asp_type in [const.CONJUNCTION, const.SEXTILE, const.SQUARE,
                     const.TRINE, const.OPPOSITION]:
        found = aspects.find(chart, asp_type)
        for asp in found:
            result.append({
                "type": asp.type,
                "obj1": asp.obj1.id,
                "obj2": asp.obj2.id,
                "exact": round(asp.orb,2)
            })
    return result

# --- Роути ---
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    name = data.get('name','Unknown')
    date = data.get('date')
    time = data.get('time')
    place = data.get('place')

    lat, lon = get_coordinates(place)
    if lat is None or lon is None:
        return jsonify({"error": "Не вдалося визначити координати місця"}), 400

    tz = get_timezone(lat, lon)
    dt_obj = parse_datetime(date, time, tz)

    # Placidus-chart через константу
    astro_dt = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz.zone)
    pos = GeoPos(lat, lon)
    try:
        chart = Chart(astro_dt, pos, hsys=const.PLACIDUS)  # Placidus через константу
    except Exception:
        chart = Chart(astro_dt, pos)  # fallback на дефолтну систему домів

    chart_file = generate_chart(chart, name)
    aspects_json = get_aspects_json(chart)

    return jsonify({
        "name": name,
        "date": date,
        "time": time,
        "place": place,
        "timezone": tz.zone,
        "aspects_json": aspects_json,
        "chart_url": f"/{CHART_FILE}"
    })

@app.route(f'/{CHART_FILE}', methods=['GET'])
def serve_chart():
    return send_from_directory('.', CHART_FILE)

# --- Health Check ---
@app.route("/health")
def health():
    return "OK", 200

# --- Запуск ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)