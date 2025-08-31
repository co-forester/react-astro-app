import os
import math
import numpy as np
from datetime import datetime as dt
from flask import Flask, request, jsonify
from flask_cors import CORS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from flatlib.chart import Chart
from flatlib import const

app = Flask(__name__)
CORS(app)

# --- Helper Functions ---
def dms_string(deg_float):
    deg = int(deg_float)
    min_float = (deg_float - deg) * 60
    minute = int(min_float)
    sec = int((min_float - minute) * 60)
    return f"{deg}°{minute}'{sec}\""

def draw_natal_chart(chart, filename="chart.png"):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'polar': True})
    ax.set_facecolor('#ffffff')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_ylim(0, 1)

    # --- Parameters ---
    r_inner = 0.65
    r_outer = 0.85
    r_house = 0.63
    r_logo = 0.55
    r_aspect = r_outer
    theta_offset = np.pi/2  # ASC at left side
    
    # --- Zodiac Ring ---
    signs = const.SIGNS
    sign_colors = ['#FFDDC1','#FFE4B5','#FFDAB9','#FFE4C4','#FFEFD5','#FFFACD',
                   '#FAF0E6','#F5F5DC','#FFF8DC','#F0E68C','#E6E6FA','#D8BFD8']
    for i, sign in enumerate(signs):
        theta1 = (i/12)*2*np.pi + theta_offset
        theta2 = ((i+1)/12)*2*np.pi + theta_offset
        ax.add_patch(Wedge((0,0), r_outer, np.degrees(theta1), np.degrees(theta2),
                           width=r_outer-r_inner, facecolor=sign_colors[i], edgecolor='k', lw=0.5))
        # Name of sign along arc
        mid_theta = (theta1 + theta2)/2
        ax.text(mid_theta, r_outer+0.03, sign, fontsize=10, ha='center', va='center', rotation=-np.degrees(mid_theta-np.pi/2),
                rotation_mode='anchor')

    # --- Houses ---
    for i in range(12):
        theta = (i/12)*2*np.pi + theta_offset
        ax.plot([theta, theta], [0, r_house], color='grey', lw=0.7, ls='--')

    # --- Planets ---
    planet_positions = {}
    for obj in chart.objects:
        deg = obj.signlon
        theta = np.radians(deg*360/360) + theta_offset
        planet_positions[obj.id] = theta
        ax.plot(theta, r_inner+0.1, 'o', color='blue')
        ax.text(theta, r_inner+0.12, obj.id, fontsize=9, ha='center', va='center')

    # --- Aspects ---
    aspect_colors = {
        'CONJUNCTION':'#FF0000',
        'OPPOSITION':'#0000FF',
        'TRINE':'#00FF00',
        'SQUARE':'#FFA500',
        'SEXTILE':'#800080'
    }
    aspects = chart.getAspects()
    for aspect in aspects:
        p1 = aspect.obj1.id
        p2 = aspect.obj2.id
        color = aspect_colors.get(aspect.type, '#000000')
        theta1 = planet_positions[p1]
        theta2 = planet_positions[p2]
        ax.plot([theta1, theta2], [r_aspect, r_aspect], color=color, lw=1.5, alpha=0.7)

    # --- ASC/MC/DSC/IC ---
    angles = {
        'ASC': chart.getObject('ASC').signlon,
        'MC': chart.getObject('MC').signlon,
        'DSC': chart.getObject('DSC').signlon,
        'IC': chart.getObject('IC').signlon
    }
    for key, deg in angles.items():
        theta = np.radians(deg*360/360) + theta_offset
        ax.text(theta, r_outer+0.05, f"{key} {dms_string(deg)}", fontsize=9, ha='center', va='center', rotation=-np.degrees(theta-np.pi/2),
                rotation_mode='anchor', color='black')

    # --- Logo Scorpio ---
    text = "Albireo Daria"
    n = len(text)
    theta_start = (7/12)*2*np.pi + theta_offset  # Start in Scorpio sector
    theta_end = (8/12)*2*np.pi + theta_offset
    thetas = np.linspace(theta_end, theta_start, n)
    for i, ch in enumerate(text):
        ax.text(thetas[i], r_logo, ch, fontsize=9, ha='center', va='center', rotation=180, color="#444444")

    # --- Save ---
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    return aspects

# --- Generate Endpoint ---
@app.route("/generate", methods=["POST"])
def generate_chart():
    try:
        data = request.json
        date = data['date']
        time = data['time']
        city = data['city']

        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(city)
        tf = TimezoneFinder()
        tz = pytz.timezone(tf.timezone_at(lng=loc.longitude, lat=loc.latitude))
        dt_utc = tz.localize(dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")).astimezone(pytz.UTC)

        chart = Chart(dt_utc, loc.latitude, loc.longitude)

        aspects = draw_natal_chart(chart)

        aspect_list = []
        for a in aspects:
            aspect_list.append({
                "obj1": a.obj1.id,
                "obj2": a.obj2.id,
                "type": a.type,
                "exact": dms_string(a.orb)
            })

        return jsonify({"status":"ok", "aspects": aspect_list, "chart_img": "/chart.png"})

    except Exception as e:
        return jsonify({"status":"error", "message": str(e)}), 500

# --- Serve Chart Image ---
@app.route("/chart.png")
def serve_chart():
    return app.send_static_file("chart.png")

# --- Health ---
@app.route("/health")
def health():
    return "OK", 200

# --- Run ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)