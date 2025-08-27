# app.py

import os
import time
import hashlib
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless режим
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

# 🧹 Автоочистка старих файлів (старше 30 днів)
def cleanup_old_charts(folder="static", days=30):
    if not os.path.exists(folder):
        return
    now = time.time()
    cutoff = now - days * 24 * 60 * 60
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if os.path.isfile(path) and filename.startswith("chart_") and filename.endswith(".png"):
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
        date_str = data.get("date")   # YYYY-MM-DD
        time_str = data.get("time")   # HH:MM
        place = data.get("place")     # Місто/адреса

        # Унікальний ключ (щоб не будувати двічі одну й ту саму карту)
        key_str = f"{name}_{date_str}_{time_str}_{place}"
        hash_key = hashlib.md5(key_str.encode("utf-8")).hexdigest()
        filename = f"chart_{hash_key}.png"
        chart_path = os.path.join("static", filename)

        # 🧹 Чистимо старі файли перед роботою
        os.makedirs("static", exist_ok=True)
        cleanup_old_charts("static", days=30)

        # Якщо файл вже існує — віддаємо готовий
        if os.path.exists(chart_path):
            return jsonify({
                "name": name,
                "date": date_str,
                "time": time_str,
                "place": place,
                "timezone": "cached",
                "chart_url": request.host_url.rstrip("/") + f"/static/{filename}"
            })

        # Якщо нема → будуємо новий
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Місце не знайдено"}), 400

        lat, lon = location.latitude, location.longitude

        tz_str = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        tz = pytz.timezone(tz_str)

        naive_dt = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(naive_dt)

        fdate = Datetime(
            local_dt.strftime("%Y/%m/%d"),
            local_dt.strftime("%H:%M"),
            local_dt.utcoffset().total_seconds() / 3600
        )
        pos = GeoPos(lat, lon)
        chart = Chart(fdate, pos)

        # Малюємо PNG
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Natal Chart - {name}")
        ax.plot([0, 1], [0, 1], "o")  # простий маркер
        ax.axis("off")

        plt.savefig(chart_path, bbox_inches="tight")
        plt.close(fig)

        return jsonify({
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "chart_url": request.host_url.rstrip("/") + f"/static/{filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)