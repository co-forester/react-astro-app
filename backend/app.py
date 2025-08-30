import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const

# ----------------- App -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Helper functions -----------------
def get_chart_data(date, time, city, country):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(f"{city}, {country}")
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    tz = pytz.timezone(tz_str)

    dt_obj = dt.strptime(f"{date} {time}", "%d-%m-%Y %H:%M")
    dt_obj = tz.localize(dt_obj)
    fdt = Datetime(dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"), tz_str)
    pos = GeoPos(location.latitude, location.longitude)
    chart = Chart(fdt, pos)
    return chart

def draw_natal_chart(chart, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(10,10))
    ax.set_xlim(-1.1,1.1)
    ax.set_ylim(-1.1,1.1)
    ax.axis('off')

    # ----------------- Zodiac circle -----------------
    circle = Circle((0,0),1,fill=False,edgecolor='black',linewidth=2)
    ax.add_patch(circle)

    # Zodiac signs positions
    zodiac = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
    for i,s in enumerate(zodiac):
        angle = math.radians(i*30 + 15)
        x = 0.9 * math.cos(angle)
        y = 0.9 * math.sin(angle)
        ax.text(x,y,s,fontsize=18,fontweight='bold',ha='center',va='center')

    # ----------------- Degrees -----------------
    for deg in range(0,360,10):
        angle = math.radians(deg)
        x = math.cos(angle)
        y = math.sin(angle)
        ax.text(1.02*x,1.02*y,str(deg)+'°',fontsize=8,ha='center',va='center')

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
        ax.text(x,y,sym,fontsize=22,fontweight='bold',ha='center',va='center')
        planet_positions[p] = (x,y)

    # ----------------- AC, DC, IC, VC -----------------
    ac_lon = chart.get(const.ASC).signlon
    dc_lon = chart.get(const.DESC).signlon
    mc_lon = chart.get(const.MC).signlon
    ic_lon = chart.get(const.IC).signlon

    ac_pos = (0.8*math.cos(math.radians(ac_lon)), 0.8*math.sin(math.radians(ac_lon)))
    dc_pos = (0.8*math.cos(math.radians(dc_lon)), 0.8*math.sin(math.radians(dc_lon)))
    mc_pos = (0.8*math.cos(math.radians(mc_lon)), 0.8*math.sin(math.radians(mc_lon)))
    ic_pos = (0.8*math.cos(math.radians(ic_lon)), 0.8*math.sin(math.radians(ic_lon)))

    ax.text(*ac_pos,'AC',fontsize=12,fontweight='bold',ha='center',va='center',color='red')
    ax.text(*dc_pos,'DC',fontsize=12,fontweight='bold',ha='center',va='center',color='blue')
    ax.text(*mc_pos,'MC',fontsize=12,fontweight='bold',ha='center',va='center',color='green')
    ax.text(*ic_pos,'IC',fontsize=12,fontweight='bold',ha='center',va='center',color='purple')

    # ----------------- Aspects -----------------
    aspect_colors = {
        'Conjunction':'red','Opposition':'blue','Trine':'green','Square':'orange','Sextile':'purple'
    }
    for a in aspects.getAspects(chart):
        x1,y1 = planet_positions.get(a.p1)
        x2,y2 = planet_positions.get(a.p2)
        color = aspect_colors.get(a.type,'gray')
        ax.add_line(Line2D([x1,x2],[y1,y2],color=color,linewidth=1.5,alpha=0.7))

    # ----------------- Logo center -----------------
    ax.text(0,0,"ASTRO\nLOGO",fontsize=14,fontweight='bold',ha='center',va='center',color='darkred')

    fig.savefig(filename, bbox_inches='tight')
    plt.close(fig)

# ----------------- Routes -----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    date = data.get("date")
    time = data.get("time")
    city = data.get("city")
    country = data.get("country")

    chart = get_chart_data(date,time,city,country)
    draw_natal_chart(chart,"chart.png")

    ac = chart.get(const.ASC).signlon
    dc = chart.get(const.DESC).signlon
    mc = chart.get(const.MC).signlon
    ic = chart.get(const.IC).signlon

    return jsonify({
        "chart":"chart.png",
        "AC":ac,
        "DC":dc,
        "MC":mc,
        "IC":ic
    })

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)