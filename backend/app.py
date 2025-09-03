# app.py — професійна натальна карта (Placidus), кеш PNG/JSON, дугові підписи, лого, DMS, ASC/MC/IC/DSC
import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt
import numpy as np

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# --- Налаштування Flask ---
app = Flask(__name__)
CORS(app)

# --- Директорії ---
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

STATIC_DIR = 'static'
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# --- Константи для карти ---
ZODIAC_SYMBOLS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
ZODIAC_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
HOUSE_COLORS = [("#fde0dd","#a50f15"),("#fa9fb5","#7a0177"),("#fcbba1","#cb181d"),("#fee0d2","#67000d"),("#fdd0a2","#e6550d"),("#fee6ce","#a63603"),("#e5f5f9","#0868ac"),("#99d8c9","#006d2c"),("#ccece6","#238b45"),("#bae4bc","#00441b"),("#f0f0f0","#636363"),("#d9d9d9","#252525")]

# --- Утиліти ---

def hash_key(*args):
    key = '|'.join(map(str,args))
    return hashlib.md5(key.encode()).hexdigest()

def cache_path(key, ext='json'):
    return os.path.join(CACHE_DIR, f'{key}.{ext}')

# --- Конвертація градусів у радіани полярної системи ---
def to_theta(deg):
    return np.deg2rad((90 - deg) % 360.0)

# --- Отримати довготу дому ---
def get_house_lon(chart, house_number):
    try:
        return float(chart.houses[house_number].lon)
    except Exception:
        return None

import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# --- Константи ---
ZODIAC_SYMBOLS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
HOUSE_COLORS = [
    ('#f9c74f', '#f9844a'), ('#90be6d', '#43aa8b'), ('#f94144', '#f3722c'),
    ('#577590', '#277da1'), ('#f8961e', '#f9c74f'), ('#43aa8b', '#90be6d'),
    ('#f3722c', '#f94144'), ('#277da1', '#577590'), ('#f9844a', '#f9c74f'),
    ('#90be6d', '#43aa8b'), ('#f94144', '#f3722c'), ('#577590', '#277da1')
]

CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# ----------------- Утиліти -----------------
def hash_request(data):
    m = hashlib.md5()
    m.update(json.dumps(data, sort_keys=True).encode())
    return m.hexdigest()

def to_theta(deg):
    # Перетворюємо градуси на радіани, 0 вгорі, за годинниковою
    return np.deg2rad((90 - deg) % 360)

def save_chart_image(fig, filename):
    path = os.path.join(CACHE_DIR, filename)
    fig.savefig(path, bbox_inches='tight', transparent=True)
    plt.close(fig)
    return path

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Статика кешу -----------------
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

# ----------------- Генерація карти -----------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        date_str = data.get("date")
        time_str = data.get("time")
        city = data.get("city")
        country = data.get("country")

        # --- Геолокація ---
        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(f"{city}, {country}")
        if not loc:
            return jsonify({"error": "Location not found"}), 400

        lat, lon = loc.latitude, loc.longitude

        # --- Часовий пояс ---
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        if not tz_str:
            tz_str = "UTC"
        tz = pytz.timezone(tz_str)
        dt_obj = tz.localize(dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))

        # --- Кешування ---
        cache_key = hash_request({"date": date_str, "time": time_str, "city": city, "country": country})
        png_file = f"{cache_key}.png"
        json_file = f"{cache_key}.json"

        if os.path.exists(os.path.join(CACHE_DIR, png_file)) and os.path.exists(os.path.join(CACHE_DIR, json_file)):
            return jsonify({
                "png": f"/cache/{png_file}",
                "data": json.load(open(os.path.join(CACHE_DIR, json_file)))
            })

        # --- Створення карти ---
        chart = Chart(Datetime(date_str, time_str, tz_str), GeoPos(lat, lon), houses='P')

        # Перевірка ASC/DSC/MC/IC
        asc = getattr(chart.get("ASC"), "lon", None)
        mc = getattr(chart.get("MC"), "lon", None)
        if asc is None or mc is None:
            return jsonify({"error": "Chart objects missing ASC or MC"}), 500
        dsc = (asc + 180) % 360
        ic = (mc + 180) % 360

        # --- Малювання карти ---
        fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'polar': True})
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        ax.set_xticks([])
        ax.set_yticks([])

        # Кільце зодіаку
        ring_radius_start = 1.10
        ring_height = 0.20
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i*30
            end = start+30
            mid = (start + 15) % 360
            center = to_theta(mid)
            width = np.deg2rad(30)
            ax.bar(
                x=center,
                height=ring_height,
                width=width,
                bottom=ring_radius_start,
                color=HOUSE_COLORS[i % 12][0],
                edgecolor=HOUSE_COLORS[i % 12][1],
                linewidth=1.2,
                zorder=3,
                align='center'
            )
            ax.text(center, ring_radius_start+ring_height/2, sym, color='black', fontsize=14,
                    ha='center', va='center', zorder=4)

        # ASC/DSC/MC/IC підписи
        outer_radius = ring_radius_start + ring_height + 0.05
        ax.text(to_theta(asc), outer_radius, 'ASC', color='yellow', ha='center', va='center')
        ax.text(to_theta(dsc), outer_radius, 'DSC', color='yellow', ha='center', va='center')
        ax.text(to_theta(mc), outer_radius, 'MC', color='yellow', ha='center', va='center')
        ax.text(to_theta(ic), outer_radius, 'IC', color='yellow', ha='center', va='center')

        # Збереження
        save_chart_image(fig, png_file)

        response_data = {
            "ASC": asc,
            "DSC": dsc,
            "MC": mc,
            "IC": ic,
            "lat": lat,
            "lon": lon,
            "tz": tz_str
        }

        with open(os.path.join(CACHE_DIR, json_file), "w") as f:
            json.dump(response_data, f)

        return jsonify({
            "png": f"/cache/{png_file}",
            "data": response_data
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Chart generation failed", "details": str(e)}), 500


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