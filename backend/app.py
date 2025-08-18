from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import matplotlib.pyplot as plt
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.get_json()
        date = data.get('date')       # "YYYY-MM-DD"
        time = data.get('time')       # "HH:MM"
        place = data.get('place')     # "Миколаїв, Україна"

        if not date or not time or not place:
            return jsonify({"error": "Missing date, time or place"}), 400

        # Геокодування
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"error": "Place not found"}), 400

        lat = location.latitude
        lon = location.longitude

        # Визначення часової зони
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_name = "UTC"

        tz = pytz.timezone(tz_name)
        
        # Розділяємо дату та час
        dt_str = f"{date} {time}"
        dt_obj = pytz.utc.localize(pytz.datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        dt_obj = dt_obj.astimezone(tz)
        
        # Отримуємо числовий часовий пояс як float
        offset_hours = dt_obj.utcoffset().total_seconds() / 3600.0

        # Створення Flatlib Datetime та Chart
        f_datetime = Datetime(date, time, offset_hours)
        f_geopos = GeoPos(lat, lon)
        chart = Chart(f_datetime, f_geopos)

        # Малюємо базову карту (приклад)
        plt.figure(figsize=(6,6))
        plt.title(f"Натальна карта: {date} {time}, {place}")
        plt.axis('off')
        plt.savefig("chart.png", bbox_inches='tight')
        plt.close()

        return jsonify({
            "message": "Chart generated successfully",
            "chart_url": "/chart.png"
        })

    except Exception as e:
        return jsonify({"error": str(e), "trace": repr(e)}), 500

@app.route('/chart.png')
def chart_png():
    try:
        return send_file('chart.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e), "trace": repr(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)