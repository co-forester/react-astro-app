import os
import math
from datetime import datetime as dt

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects as fasp
from flatlib import const

app = Flask(__name__)
CORS(app)

# --- COLORS ---
PLANET_COLORS = {
    const.SUN: "#FFA500",
    const.MOON: "#1E90FF",
    const.MERCURY: "#32CD32",
    const.VENUS: "#FF69B4",
    const.MARS: "#FF4500",
    const.JUPITER: "#9370DB",
    const.SATURN: "#708090",
    const.URANUS: "#40E0D0",
    const.NEPTUNE: "#0000FF",
    const.PLUTO: "#8B0000",
}

ASPECT_COLORS = {
    const.CONJUNCTION: "#FF0000",
    const.SEXTILE: "#00FF00",
    const.SQUARE: "#FF00FF",
    const.TRINE: "#0000FF",
    const.OPPOSITION: "#FFA500",
}

# --- Zodiac names and symbols ---
ZODIAC_SIGNS = [
    ("Aries", "♈"), ("Taurus", "♉"), ("Gemini", "♊"), ("Cancer", "♋"),
    ("Leo", "♌"), ("Virgo", "♍"), ("Libra", "♎"), ("Scorpio", "♏"),
    ("Sagittarius", "♐"), ("Capricorn", "♑"), ("Aquarius", "♒"), ("Pisces", "♓")
]

# --- Helper functions ---
def dms(degree):
    deg = int(degree)
    min_ = int((degree - deg) * 60)
    sec = int(((degree - deg) * 60 - min_) * 60)
    return f"{deg}°{min_}'{sec}\""

def polar_to_cartesian(r, theta):
    return r * math.cos(theta), r * math.sin(theta)

# --- Generate chart image ---
def generate_chart(data):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'polar': True})
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location("E")
    ax.set_ylim(0, 1.2)
    ax.axis('off')

    # --- Draw zodiac sectors ---
    for i, (name, symbol) in enumerate(ZODIAC_SIGNS):
        start = 2*math.pi * i/12
        end = 2*math.pi * (i+1)/12
        ax.bar(
            x=(start+end)/2,
            height=0.6,
            width=end-start,
            bottom=0.6,
            color=f"C{i%10}",
            alpha=0.2,
            edgecolor="k"
        )
        # Sign symbol and name along arc
        th = (start+end)/2
        ax.text(th, 0.9, symbol, fontsize=20, ha='center', va='center', color="#444")
        ax.text(th, 1.05, name, fontsize=10, ha='center', va='center', color="#444")

    # --- Draw planets ---
    planets = []
    for p in data['planets']:
        degree = p['degree'] * math.pi/180
        ax.plot([degree], [0.75], 'o', color=PLANET_COLORS[p['name']], markersize=12)
        x, y = polar_to_cartesian(0.75, degree)
        ax.text(degree, 0.78, p['symbol'], fontsize=12, ha='center', va='center')

    # --- Draw aspects as chords ---
    for asp in data['aspects']:
        deg1 = asp['from_degree'] * math.pi/180
        deg2 = asp['to_degree'] * math.pi/180
        ax.plot([deg1, deg2], [0.75, 0.75], color=ASPECT_COLORS[asp['type']], lw=1.5)

    # --- ASC/MC/DSC/IC ---
    angles = data['angles']
    for name, deg in angles.items():
        theta = deg * math.pi/180
        ax.text(theta, 1.15, name + " " + dms(deg), fontsize=10, ha='center', va='center', fontweight='bold')

    # --- Logo in Scorpio sector ---
    sc_index = 7
    start = 2*math.pi * sc_index/12
    end = 2*math.pi * (sc_index+1)/12
    theta_logo = np.linspace(end-0.05, start+0.05, len("Albireo Daria"))
    r_logo = 0.55
    for i, ch in enumerate("Albireo Daria"):
        th = theta_logo[i]
        ax.text(th, r_logo, ch, fontsize=10, ha='center', va='center', rotation=180, color="#444")

    # --- Table of aspects ---
    aspect_table = [[asp['from'], asp['type'], asp['to'], dms(asp['angle'])] for asp in data['aspects']]
    columns = ["From", "Aspect", "To", "Angle"]
    table = plt.table(cellText=aspect_table, colLabels=columns, loc='bottom', cellLoc='center', colColours=['#eee']*4)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Save figure
    plt.savefig("chart.png", bbox_inches='tight')
    plt.close(fig)
    return "chart.png"

# --- Routes ---
@app.route("/generate", methods=["POST"])
def generate():
    try:
        req = request.get_json()
        # --- Parse date/time ---
        date = req['date']
        time = req['time']
        city = req['city']
        dt_obj = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

        # --- Geocode ---
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(city)
        if not location:
            return jsonify({"status": "error", "message": "City not found"}), 400
        tz_str = TimezoneFinder().timezone_at(lng=location.longitude, lat=location.latitude)
        tz = pytz.timezone(tz_str)
        dt_obj = tz.localize(dt_obj)

        fdt = Datetime(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute, tz_str)
        chart = Chart(fdt, GeoPos(location.latitude, location.longitude))

        # --- Collect planet positions ---
        planets = []
        for name in [const.SUN,const.MOON,const.MERCURY,const.VENUS,const.MARS,const.JUPITER,const.SATURN,const.URANUS,const.NEPTUNE,const.PLUTO]:
            obj = chart.get(name)
            planets.append({
                "name": name,
                "symbol": const.SYMBOLS[name],
                "degree": obj.lon
            })

        # --- Collect angles ASC/MC/DSC/IC ---
        angles = {}
        for angle in [const.ASC, const.MC, const.DSC, const.IC]:
            obj = chart.get(angle)
            angles[angle] = obj.lon

        # --- Collect aspects ---
        aspects = []
        for a in fasp.getAspects(chart):
            aspects.append({
                "from": a.obj1.name,
                "to": a.obj2.name,
                "type": a.type,
                "angle": a.angle,
                "from_degree": a.obj1.lon,
                "to_degree": a.obj2.lon
            })

        chart_file = generate_chart({"planets": planets, "angles": angles, "aspects": aspects})
        return jsonify({"status": "ok", "chart": chart_file, "planets": planets, "aspects": aspects})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Health ---
@app.route("/health")
def health():
    return "OK", 200

# --- Run ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)