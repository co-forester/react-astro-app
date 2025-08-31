import os
import math
from datetime import datetime
from flask import Flask, request, jsonify, send_file
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
from flatlib import aspects as fl_aspects

app = Flask(__name__)
CORS(app)

@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.get_json()
    name = data.get("name", "Народжений")
    date_str = data.get("date")  # формат YYYY-MM-DD
    time_str = data.get("time")  # формат HH:MM
    place_str = data.get("place")

    try:
        # Геолокація
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place_str)
        if not location:
            return jsonify({"message": f"Місто не знайдено: {place_str}", "status": "error"}), 400
        lat, lon = location.latitude, location.longitude
        geo = GeoPos(lat, lon)

        # Часовий пояс
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        if not tz_name:
            tz_name = "UTC"
        tz = pytz.timezone(tz_name)

        # datetime
        dt_naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_aware = tz.localize(dt_naive)
        fdt = Datetime(dt_aware.year, dt_aware.month, dt_aware.day, dt_aware.hour, dt_aware.minute, 0, tz_name)

        chart = Chart(fdt, geo)

        # Аспекти
        aspects_list = []
        planets = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto']
        for i, p1 in enumerate(planets):
            for p2 in planets[i+1:]:
                for a in fl_aspects.MAJOR_ASPECTS:
                    if chart.get(p1).isAspect(chart.get(p2), a):
                        angle = chart.get(p1).aspect(chart.get(p2)).angle
                        aspects_list.append({
                            "planet1": p1,
                            "planet2": p2,
                            "type": a.name,
                            "angle": f"{angle:.1f}°",
                            "color": a.color
                        })

        # Малювання карти
        fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)

        # Сектори будинків
        for i in range(12):
            start = i * 30
            ax.bar(math.radians(start), 1, width=math.radians(30), color=plt.cm.Pastel1(i), edgecolor='white', alpha=0.5)

        # Логотип/ім'я в центрі
        ax.text(0,0, name, fontsize=14, ha='center', va='center', fontweight='bold')

        # Плоти планети на колі (просте розташування по градусах)
        for p in planets:
            body = chart.get(p)
            pos = body.signlon
            ax.plot(math.radians(pos), 1, 'o', label=p)

        ax.set_rticks([])
        ax.set_yticklabels([])
        ax.set_xticks([])
        ax.set_xticklabels([])

        chart_file = "chart.png"
        plt.savefig(chart_file, bbox_inches='tight', dpi=150)
        plt.close(fig)

        return jsonify({
            "chart_url": f"/chart.png",
            "aspects_json": aspects_list
        })
    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@app.route("/chart.png")
def send_chart():
    return send_file("chart.png", mimetype='image/png')

# --- Health ---
@app.route('/health')
def health():
    return "OK", 200

# --- Run ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)