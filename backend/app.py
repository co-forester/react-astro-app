from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.json

    # --- Обробка дати/часу ---
    dt_str = data.get("datetime")
    if dt_str:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            date = dt.date().isoformat()
            time = dt.time().strftime("%H:%M")
        except ValueError:
            return jsonify({"error": f"Invalid datetime format: {dt_str}"}), 400
    else:
        date = data.get("date")
        time = data.get("time")
        if not (date and time):
            return jsonify({"error": "Missing 'datetime' or 'date+time' field"}), 400

    # --- Обробка місця ---
    place = data.get("place")
    if not place:
        return jsonify({"error": "Missing 'location'/'place' field"}), 400

    first_name = data.get("firstName", "")
    last_name = data.get("lastName", "")

    try:
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": f"Location not found: {place}"}), 400

        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        tz = pytz.timezone(timezone_str)
        dt_obj = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        dt_obj = tz.localize(dt_obj)
        fdt = Datetime(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute, tz=timezone_str)
        pos = GeoPos(location.latitude, location.longitude)

        chart = Chart(f"{date} {time}", pos, charttype='natal')

        # --- Створення зображення карти ---
        fig, ax = plt.subplots(figsize=(6,6))
        ax.text(0.5, 0.5, f"{first_name} {last_name}\n{date} {time}\n{place}", ha='center')
        plt.axis('off')
        chart_file = "chart.png"
        plt.savefig(chart_file, bbox_inches='tight', dpi=150)
        plt.close(fig)

        # --- Таблиця аспектів ---
        aspects_list = []
        for obj1 in chart.objects:
            for obj2 in chart.objects:
                if obj1 != obj2:
                    asp = aspects.getAspect(obj1, obj2)
                    if asp:
                        aspects_list.append({
                            "object1": obj1.id,
                            "object2": obj2.id,
                            "aspect": asp.type,
                            "orb": asp.orb
                        })

        return jsonify({
            "chart_image_url": f"/{chart_file}",
            "aspects_table_html": "<pre>" + str(aspects_list) + "</pre>",
            "raw_data": {
                "firstName": first_name,
                "lastName": last_name,
                "date": date,
                "time": time,
                "place": place,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "timezone": timezone_str
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chart.png")
def get_chart_image():
    if os.path.exists("chart.png"):
        return send_file("chart.png", mimetype="image/png")
    else:
        return jsonify({"error": "Chart not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)