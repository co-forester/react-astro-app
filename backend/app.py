import os
import math
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
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

# --- Helper functions ---
def format_dms(value):
    deg = int(value)
    min_float = (value - deg) * 60
    minute = int(min_float)
    second = int((min_float - minute) * 60)
    return f"{deg}°{minute}'{second}''"

# --- Generate chart image ---
def generate_chart_image(chart):
    fig, ax = plt.subplots(figsize=(10,10), subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1)  # counter-clockwise
    ax.set_theta_offset(math.pi/2)  # 0 at top
    ax.set_facecolor('white')
    
    # Draw zodiac circle (wider)
    zodiac_r = 1.5
    ax.set_ylim(0, zodiac_r)
    
    # Draw houses sectors with pastel colors
    for i in range(12):
        start = math.radians(i*30)
        end = math.radians((i+1)*30)
        ax.fill_between([start,end], 0, zodiac_r, color=plt.cm.Pastel1(i/12), alpha=0.3)

    # Draw zodiac symbols along circle
    zodiac_symbols = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
    zodiac_names = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    for i, sym in enumerate(zodiac_symbols):
        angle = math.radians(i*30 + 15)
        ax.text(angle, zodiac_r*1.02, sym, fontsize=20, ha='center', va='center')
        ax.text(angle, zodiac_r*1.1, zodiac_names[i], fontsize=10, ha='center', va='center', rotation=-math.degrees(angle)+90)
    
    # Draw aspects
    aspect_colors = {
        'Conjunction':'red',
        'Opposition':'blue',
        'Trine':'green',
        'Square':'orange',
        'Sextile':'purple'
    }
    planets = chart.planets()
    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets):
            if i < j:
                asp = chart.getAspect(p1, p2)
                if asp:
                    color = aspect_colors.get(asp.type, 'gray')
                    theta1 = math.radians(p1.lon)
                    theta2 = math.radians(p2.lon)
                    ax.plot([theta1, theta2], [0.9*zodiac_r,0.9*zodiac_r], color=color, lw=1)

    # TODO: draw ASC/MC/DSC/IC labels outside circle with DMS
    # TODO: add Scorpio logo along the symbol

    # Save figure
    if not os.path.exists('static'):
        os.makedirs('static')
    path = os.path.join('static','chart.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    return path

# --- API Endpoints ---
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    date_str = data.get('date')
    time_str = data.get('time')
    location = data.get('location')
    try:
        geolocator = Nominatim(user_agent='astroapp')
        loc = geolocator.geocode(location)
        tzf = TimezoneFinder()
        tzname = tzf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        tz = pytz.timezone(tzname)
        dt_utc = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        dt_local = tz.localize(dt_utc)
        fdt = Datetime(date_str, time_str, tzname)
        pos = GeoPos(loc.latitude, loc.longitude)
        chart = Chart(fdt, pos)

        path = generate_chart_image(chart)

        return jsonify({
            'status':'ok',
            'chart_url':'/'+path
        })
    except Exception as e:
        return jsonify({'status':'error','message':str(e)})

# --- Health ---
@app.route('/health')
def health():
    return "OK", 200

# --- Run ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)