import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const
from flatlib.aspect import Aspect

app = Flask(__name__)
CORS(app)

# ----------------- Основні функції -----------------
def geocode_location(location_name):
    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(location_name)
    if loc:
        return loc.latitude, loc.longitude
    return None, None

def get_timezone(lat, lon, date):
    tf = TimezoneFinder()
    tzname = tf.timezone_at(lat=lat, lng=lon)
    tz = pytz.timezone(tzname) if tzname else pytz.utc
    return tz

def draw_natal_chart(chart, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(10,10))
    ax.set_xlim(-1.2,1.2)
    ax.set_ylim(-1.2,1.2)
    ax.axis('off')

    # ----------------- Zodiac circle -----------------
    zodiac_colors = ['#FFDDC1','#FFE4B5','#FFFACD','#E0FFFF','#F0E68C','#FAFAD2',
                     '#D8BFD8','#E6E6FA','#F5DEB3','#FFE4E1','#F0FFF0','#F5F5DC']
    zodiac = ['♈','♉','♊','♋','♌','♍','♎', None,'♐','♑','♒','♓']  # None для Скорпіона

    for i in range(12):
        angle_start = math.radians(i*30)
        angle_end = math.radians((i+1)*30)
        wedge = matplotlib.patches.Wedge(center=(0,0), r=1.0, theta1=math.degrees(angle_start),
                                         theta2=math.degrees(angle_end), facecolor=zodiac_colors[i], alpha=0.3)
        ax.add_patch(wedge)

        # Символи знаків
        angle_mid = math.radians(i*30 + 15)
        x = 0.9 * math.cos(angle_mid)
        y = 0.9 * math.sin(angle_mid)
        if zodiac[i]:
            ax.text(x, y, zodiac[i], fontsize=18, fontweight='bold', ha='center', va='center')
        else:
            # Логотип для Скорпіона
            logo_circle = Circle((x,y), 0.05, color='darkred', ec='black', lw=1.5)
            ax.add_patch(logo_circle)
            ax.text(x, y, "LOGO", fontsize=10, fontweight='bold', ha='center', va='center', color='white')

    # ----------------- Degrees -----------------
    for deg in range(0,360,10):
        angle = math.radians(deg)
        x = 1.02 * math.cos(angle)
        y = 1.02 * math.sin(angle)
        ax.text(x, y, f"{deg}°", fontsize=8, ha='center', va='center', color='gray')

    # ----------------- Houses -----------------
    house_colors = plt.cm.tab20c.colors
    for i in range(12):
        angle = math.radians(i*30)
        x = [0, math.cos(angle)]
        y = [0, math.sin(angle)]
        ax.plot(x, y, color=house_colors[i%len(house_colors)], lw=2)
        # Підписи домів
        x_text = 1.05 * math.cos(angle + math.radians(15))
        y_text = 1.05 * math.sin(angle + math.radians(15))
        ax.text(x_text, y_text, f"House {i+1}", fontsize=10, ha='center', va='center', color=house_colors[i%len(house_colors)], fontweight='bold')

    # ----------------- Planets -----------------
    planet_symbols = {
        const.SUN:'☉', const.MOON:'☽', const.MERCURY:'☿', const.VENUS:'♀',
        const.MARS:'♂', const.JUPITER:'♃', const.SATURN:'♄',
        const.URANUS:'♅', const.NEPTUNE:'♆', const.PLUTO:'♇'
    }
    planet_positions = {}
    for p,sym in planet_symbols.items():
        obj = chart.get(p)
        angle = math.radians(obj.signlon)
        x = 0.7 * math.cos(angle)
        y = 0.7 * math.sin(angle)
        ax.text(x, y, sym, fontsize=22, fontweight='bold', ha='center', va='center', color='navy')
        planet_positions[p] = (x,y)

    # ----------------- Aspects -----------------
    aspect_colors = {
        'Conjunction':'red','Opposition':'blue','Trine':'green','Square':'orange','Sextile':'purple'
    }
    for a in chart.getAspects():
        x1,y1 = planet_positions.get(a.p1)
        x2,y2 = planet_positions.get(a.p2)
        color = aspect_colors.get(a.type,'gray')
        lw = 2 if a.type in ['Conjunction','Opposition'] else 1.2
        ax.add_line(Line2D([x1,x2],[y1,y2],color=color,linewidth=lw,alpha=0.7))

    # ----------------- Central Logo -----------------
    central_circle = Circle((0,0), 0.12, color='darkred', ec='black', lw=2)
    ax.add_patch(central_circle)
    ax.text(0,0,"ASTRO\nLOGO", fontsize=16, fontweight='bold', ha='center', va='center', color='white')

    fig.savefig(filename, bbox_inches='tight')
    plt.close(fig)

# ----------------- Routes -----------------
@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.json
    date_str = data.get("date")  # 'YYYY-MM-DD'
    time_str = data.get("time")  # 'HH:MM'
    location = data.get("location")  # місто

    lat, lon = geocode_location(location)
    if lat is None:
        return jsonify({"error":"Location not found"}), 400

    tz = get_timezone(lat, lon, date_str)
    dt_utc = tz.localize(dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")).astimezone(pytz.utc)
    chart = Chart(dt_utc, lat, lon, hsys='P')  # Placidus

    draw_natal_chart(chart, filename="chart.png")

    return jsonify({
        "planets": {p:str(chart.get(p).sign) for p in [
            const.SUN,const.MOON,const.MERCURY,const.VENUS,const.MARS,
            const.JUPITER,const.SATURN,const.URANUS,const.NEPTUNE,const.PLUTO
        ]},
        "chart_image": "/chart.png"
    })

@app.route("/chart.png")
def serve_chart():
    return send_from_directory(os.getcwd(), "chart.png")




@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)