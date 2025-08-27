# app.py

import os
import time
import hashlib
from datetime import datetime as dt

from flask import Flask, request, jsonify
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
from flatlib import aspects

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

# 🧹 Очистка старих файлів старше 30 днів
def cleanup_old_charts(folder="static", days=30):
    if not os.path.exists(folder):
        return
    now = time.time()
    cutoff = now - days * 24 * 60 * 60
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if os.path.isfile(path) and filename.startswith("chart_"):
            if os.path.getmtime(path) < cutoff:
                try:
                    os.remove(path)
                    print(f"🧹 Видалено старий файл: {filename}")
                except Exception as e:
                    print(f"⚠️ Не вдалось видалити {filename}: {e}")

@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        name = data.get("name", "Person")
        date_str = data.get("date")
        time_str = data.get("time")
        place = data.get("place")

        # Хеш для кешу
        key_str = f"{name}_{date_str}_{time_str}_{place}"
        hash_key = hashlib.md5(key_str.encode("utf-8")).hexdigest()
        png_file = f"chart_{hash_key}.png"
        aspects_file = f"chart_{hash_key}_aspects.json"
        png_path = os.path.join("static", png_file)
        aspects_path = os.path.join("static", aspects_file)

        os.makedirs("static", exist_ok=True)
        cleanup_old_charts("static", days=30)

        # Якщо файли існують — віддаємо їх
        if os.path.exists(png_path) and os.path.exists(aspects_path):
            with open(aspects_path, "r", encoding="utf-8") as f:
                aspects_data = f.read()
            return jsonify({
                "name": name,
                "date": date_str,
                "time": time_str,
                "place": place,
                "timezone": "cached",
                "chart_url": request.host_url.rstrip("/") + f"/static/{png_file}",
                "aspects_json": aspects_data
            })

        # Інакше будуємо нові
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400

        lat, lon = location.latitude, location.longitude
        tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        tz = pytz.timezone(tz_str)

        naive_dt = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive_dt)
        fdate = Datetime(local_dt.strftime("%Y/%m/%d"),
                         local_dt.strftime("%H:%M"),
                         local_dt.utcoffset().total_seconds() / 3600)
        pos = GeoPos(lat, lon)
        chart = Chart(fdate, pos)

        # Генерація аспектів
        aspects_list = []
        objs = chart.objects
        for i, obj1 in enumerate(objs):
            for obj2 in objs[i+1:]:
                for asp in aspects.major:
                    if asp.isAspect(obj1, obj2):
                        aspects_list.append({
                            "object1": str(obj1),
                            "object2": str(obj2),
                            "type": asp.type,
                            "angle": asp.angle
                        })

        # Збереження аспектів
        import json
        with open(aspects_path, "w", encoding="utf-8") as f:
            json.dump(aspects_list, f, ensure_ascii=False, indent=2)

        # Малюємо PNG
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Natal Chart - {name}")
        ax.plot([0, 1], [0, 1], "o")
        ax.axis("off")
        plt.savefig(png_path, bbox_inches="tight")
        plt.close(fig)

        return jsonify({
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "chart_url": request.host_url.rstrip("/") + f"/static/{png_file}",
            "aspects_json": aspects_list
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)