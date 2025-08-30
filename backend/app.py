import os
import math
from datetime import datetime as dt, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

def clean_cache():
    now = dt.now()
    for filename in os.listdir(CACHE_DIR):
        path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(path):
            mtime = dt.fromtimestamp(os.path.getmtime(path))
            if now - mtime > timedelta(days=30):
                os.remove(path)

def generate_chart_image(chart, filename):
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
    ax.set_theta_zero_location('E')  # 0° вліво
    ax.set_theta_direction(-1)  # за годинниковою стрілкою

    # Градуси
    for deg in range(0, 360, 10):
        rad = math.radians(deg)
        length = 0.05 if deg % 30 else 0.1
        ax.plot([rad, rad], [1-length, 1], color='black', lw=1)
        if deg % 30 == 0:
            ax.text(rad, 1.1, f"{deg}°", ha='center', va='center', fontsize=10)

    # Центр
    ax.text(0, 0, "Натальна карта", ha='center', va='center', fontsize=12, fontweight='bold')

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0,1)
    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close(fig)

@app.route("/generate", methods=["POST"])
def generate():
    clean_cache()
    data = request.json

    city_name = data.get("city", "")
    date_str = data.get("date", "")
    time_str = data.get("time", "")

    if not city_name or not date_str or not time_str:
        return jsonify({"error": "Не вдалося знайти місто, дату або час"}), 400

    # Унікальний ключ для кешу
    cache_filename = f"{city_name}_{date_str}_{time_str}.png".replace(" ", "_").replace("/", "-")
    cache_path = os.path.join(CACHE_DIR, cache_filename)
    if os.path.exists(cache_path):
        return send_file(cache_path, mimetype='image/png')

    # Геокодування
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(city_name)
    if not location:
        return jsonify({"error": "Не вдалося знайти місто"}), 400
    lat, lon = location.latitude, location.longitude

    # Таймзона
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
    tz = pytz.timezone(tz_name)
    dt_obj = tz.localize(dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))

    # Flatlib Datetime
    astro_dt = Datetime(dt_obj.strftime("%Y/%m/%d"), dt_obj.strftime("%H:%M"), tz_name)
    pos = GeoPos(lat, lon)
    chart = Chart(astro_dt, pos, hsys="P")

    # Генерація картинки
    generate_chart_image(chart, cache_path)

    return send_file(cache_path, mimetype='image/png')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)