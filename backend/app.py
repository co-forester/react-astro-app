import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from flatlib.chart import Chart
from flatlib import const

app = Flask(__name__)
CORS(app)

# Директорія кешу
cache_dir = "cache"
os.makedirs(cache_dir, exist_ok=True)

@app.route("/health")
def health():
    return "OK", 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    name = data.get("name", "")
    date_str = data.get("date", "")
    time_str = data.get("time", "")
    place = data.get("place", "")

    try:
        # Геокодування
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400
        lat, lon = location.latitude, location.longitude

        # Часова зона
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_str)
        dt_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_obj = tz.localize(dt_obj)

        # Створюємо ключ для кешу
        key = f"{name}_{date_str}_{time_str}_{place}".replace(" ", "_")
        chart_path = os.path.join(cache_dir, f"{key}.png")
        json_cache_path = os.path.join(cache_dir, f"{key}.json")

        # Створення натальної карти через Flatlib
        chart = Chart(dt_obj, lat, lon, const.PLACIDUS)

        # Обчислення аспектів
        aspect_list = []
        for obj1 in chart.objects:
            for obj2 in chart.objects:
                if obj1 != obj2:
                    asp = chart.aspect(obj1, obj2)
                    if asp:
                        aspect_list.append({
                            "obj1": obj1.id, "obj2": obj2.id,
                            "type": asp.type, "angle": asp.angle
                        })

        # Малювання карти
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_facecolor("#f0f0f0")
        ax.text(0.5, 0.5, name, ha="center", va="center", fontsize=12, color="blue")
        try:
            plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        finally:
            plt.close(fig)

        # Підготувати результат і кешувати JSON
        chart_url = f"{request.host_url.rstrip('/')}/cache/{key}.png"
        out = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "aspects_json": aspect_list,
            "chart_url": chart_url
        }
        with open(json_cache_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        return jsonify(out)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)