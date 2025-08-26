import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return "Server is healthy", 200

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.get_json()

    # Перевірка полів
    if 'datetime' not in data or 'place' not in data:
        return jsonify({"error": "Missing 'datetime' or 'place' field"}), 400

    dt_str = data['datetime']  # формат: 'YYYY-MM-DD HH:MM'
    place_name = data['place']  # формат: 'Місто, Країна'

    # Парсинг дати та часу
    try:
        date_part, time_part = dt_str.split(' ')
        year, month, day = map(int, date_part.split('-'))
        hour, minute = map(int, time_part.split(':'))
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400

    # Геокодування
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(place_name)
    if not location:
        return jsonify({"error": "Location not found"}), 400

    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    if not tz_str:
        tz_str = 'UTC'

    tz = pytz.timezone(tz_str)
    dt_obj = pytz.UTC.localize(
        pytz.datetime.datetime(year, month, day, hour, minute)
    ).astimezone(tz)

    geo = GeoPos(location.latitude, location.longitude)
    dt = Datetime(dt_obj.year, dt_obj.month, dt_obj.day,
                  dt_obj.hour, dt_obj.minute, dt_obj.utcoffset().total_seconds() / 3600)

    # Створення натальної карти
    chart = Chart(dt, geo, hsys='P')  # Placidus

    # Збір планет та основних точок
    points = {}
    for obj in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
                'Asc', 'MC']:
        points[obj] = chart.get(obj).sign

    # Розрахунок аспектів
    aspect_list = []
    for i, obj1 in enumerate(['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                              'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']):
        for obj2 in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                     'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
            if obj1 >= obj2:
                continue
            asp = aspects.getAspect(chart.get(obj1), chart.get(obj2))
            if asp:
                aspect_list.append({
                    "from": obj1,
                    "to": obj2,
                    "type": asp.type
                })

    # Малювання карти
    fig, ax = plt.subplots(figsize=(8,8))
    circle = plt.Circle((0,0), 1, color='lightyellow', fill=True)
    ax.add_artist(circle)

    # Зодіак по колу
    zodiac = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
              'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    for i, sign in enumerate(zodiac):
        angle = (360/12) * i
        x = 0.85 * plt.cos(plt.radians(angle))
        y = 0.85 * plt.sin(plt.radians(angle))
        ax.text(x, y, sign, ha='center', va='center', fontsize=10, rotation=-angle+90)

    # Планети
    for obj, sign in points.items():
        idx = zodiac.index(sign)
        angle = (360/12) * idx
        x = 0.7 * plt.cos(plt.radians(angle))
        y = 0.7 * plt.sin(plt.radians(angle))
        ax.text(x, y, obj, ha='center', va='center', fontsize=9, color='blue')

    # Центр: логотип
    logo_path = 'logo.png'
    if os.path.exists(logo_path):
        logo = mpimg.imread(logo_path)
        ax.imshow(logo, extent=[-0.2,0.2,-0.2,0.2])

    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)
    ax.axis('off')
    plt.savefig('chart.png', dpi=150)
    plt.close(fig)

    response = {
        "planets": points,
        "aspects": aspect_list,
        "chart_image": "/chart.png"
    }
    return jsonify(response)

@app.route('/chart.png')
def get_chart_image():
    return send_file('chart.png', mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)