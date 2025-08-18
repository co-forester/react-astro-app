from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.get_json()
        date = data['date']           # "1972-12-06"
        time = data['time']           # "01:25"
        place_name = data['place']    # "Миколаїв, Україна"

        # Отримання координат через словник (можна замінити на геокодер)
        places = {
            "Миколаїв, Україна": (46.9750, 31.9946),
        }
        if place_name not in places:
            return jsonify({"error": "Unknown place"}), 400
        lat, lon = places[place_name]

        # Визначаємо часовий пояс
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if timezone_str is None:
            timezone_str = 'Europe/Kiev'  # резервний варіант

        tz = pytz.timezone(timezone_str)
        local_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        local_dt = tz.localize(local_dt)
        offset_hours = local_dt.utcoffset().total_seconds() / 3600  # float

        # Створення Flatlib Datetime та GeoPos
        dt = Datetime(date, time, float(offset_hours))
        pos = GeoPos(lat, lon)

        chart = Chart(dt, pos, IDs=const.LIST_OBJECTS)

        # Малюємо дуже просту натальну карту (замінити на власну логіку)
        plt.figure(figsize=(6,6))
        plt.title(f'Natal Chart: {place_name} {date} {time}')
        plt.text(0.5, 0.5, 'Тут можна додати планети та аспекти', ha='center')
        plt.savefig('chart.png')
        plt.close()

        return jsonify({"message": "Chart generated", "chart_url": "/chart.png"})
    except Exception as e:
        return jsonify({"error": str(e), "trace": repr(e)}), 500

@app.route('/chart.png')
def chart_png():
    return send_file('chart.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)