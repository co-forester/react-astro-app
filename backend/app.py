# app.py — професійна натальна карта з повною роботою всіх блоків

import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from matplotlib.patches import Wedge
import matplotlib.colors as mcolors

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz

import swisseph as swe
from flatlib.chart import Chart
from flatlib import const

# ----------------- Конфіг -----------------
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

ZODIAC_SYMBOLS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
ZODIAC_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
HOUSE_COLORS = [(('#222222','#555555'))]*12  # тимчасово, можна кастомізувати
PLANETS = [const.SUN,const.MOON,const.MERCURY,const.VENUS,const.MARS,
           const.JUPITER,const.SATURN,const.URANUS,const.NEPTUNE,const.PLUTO]
ASPECTS = [const.CONJUNCTION,const.SEXTILE,const.SQUARE,const.TRINE,const.OPPOSITION]

# ----------------- Flask -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Утиліти -----------------
def to_theta_global(degree):
    return np.deg2rad(90.0 - float(degree))

def draw_natal_chart(chart, logo_text="LOGO", logo_sign=None):
    # --- 1) Підготовка фігури ---
    fig, ax = plt.subplots(figsize=(15,15), subplot_kw={'projection':'polar'})
    ax.set_theta_zero_location('E')  # ASC на заході
    ax.set_theta_direction(-1)  # проти годинникової стрілки
    ax.set_ylim(0,1.5)
    ax.axis('off')

    # --- 2) ASC/MC/IC/DSC ---
    asc_lon = chart.get(const.ASC).lon
    mc_lon = chart.get(const.MC).lon
    ic_lon = (asc_lon + 180) % 360
    dsc_lon = (mc_lon + 180) % 360
    angles = {'ASC':asc_lon,'MC':mc_lon,'IC':ic_lon,'DSC':dsc_lon}

    for key, lon in angles.items():
        theta = np.deg2rad(lon)
        r_start = 0
        r_end = 1.9
        ax.plot([theta,theta],[r_start,r_end],color="yellow",lw=2,zorder=7)
        ax.text(theta, r_end+0.03,key, color="yellow", fontsize=10,
                ha="center", va="center", fontweight="bold", zorder=8)

    # --- 3) Планети ---
    for pl in PLANETS:
        try:
            obj = chart.get(pl)
            lon = obj.lon
            theta = np.deg2rad((lon - asc_lon) % 360)
            r = 1.5
            ax.plot(theta,r,'o',color='white',markersize=10,zorder=6)
            ax.text(theta,r+0.05,pl,color='white',ha='center',va='center',fontsize=9,zorder=6)
        except:
            continue

    # --- 4) Кільце зодіаку ---
    ring_radius_start = 1.40
    ring_height = 0.30
    for i, sym in enumerate(ZODIAC_SYMBOLS):
        start = i * 30.0
        end = start + 30.0
        span = (end - start) % 360.0
        mid = (start + span/2.0) % 360.0
        center = np.deg2rad((mid - asc_lon) % 360)
        width = np.deg2rad(span)
        ax.bar(
            x=center,
            height=ring_height,
            width=width,
            bottom=ring_radius_start,
            color=HOUSE_COLORS[i % 12][0],
            edgecolor=HOUSE_COLORS[i % 12][1],
            linewidth=1.2,
            zorder=3,
            align='center'
        )
        ax.plot([np.deg2rad((start - asc_lon) % 360)]*2,
                [ring_radius_start, ring_radius_start + ring_height + 0.01],
                color="white", lw=1.2, zorder=4)
        symbol_r = ring_radius_start + ring_height - 0.02
        label_r = ring_radius_start + 0.05
        if ZODIAC_NAMES[i] == logo_sign:
            ax.text(center, label_r, logo_text,
                    fontsize=12, ha="center", va="center",
                    color="#FFD700", fontweight="bold",
                    rotation=(mid + 90) % 360, rotation_mode="anchor", zorder=6)
        else:
            ax.text(center, symbol_r, sym,
                    fontsize=18, ha="center", va="center",
                    color="#ffffff", fontweight="bold",
                    rotation=(mid + 90) % 360, rotation_mode="anchor", zorder=6)
            ax.text(center, label_r, ZODIAC_NAMES[i],
                    fontsize=9, ha="center", va="center",
                    color="#ffffff", rotation=(mid + 90) % 360,
                    rotation_mode="anchor", zorder=5)
        for deg_mark in range(0, 31, 5):
            theta_deg = np.deg2rad((start + deg_mark - asc_lon) % 360)
            r_start = ring_radius_start + 0.01
            r_end = ring_radius_start + (0.02 if deg_mark % 10 == 0 else 0.015)
            ax.plot([theta_deg, theta_deg], [r_start, r_end], color="#faf6f7", lw=1, zorder=2)

    # --- 5) Аспекти ---
    aspect_colors = {const.CONJUNCTION:'#FFD700',const.OPPOSITION:'#FF4500',
                     const.SQUARE:'#1E90FF',const.TRINE:'#32CD32',const.SEXTILE:'#FF69B4'}
    for a in ASPECTS:
        for pl1 in PLANETS:
            for pl2 in PLANETS:
                if pl1 >= pl2:
                    continue
                try:
                    obj1 = chart.get(pl1)
                    obj2 = chart.get(pl2)
                    diff = abs((obj1.lon - obj2.lon) % 360)
                    if abs(diff - getattr(const,a)) < 1.0:
                        theta1 = np.deg2rad((obj1.lon - asc_lon) % 360)
                        theta2 = np.deg2rad((obj2.lon - asc_lon) % 360)
                        ax.plot([theta1,theta2],[1.2,1.2],color=aspect_colors[a],lw=1.5,zorder=4)
                except:
                    continue

    # --- 6) Логотип в центр ---
    ax.text(0,0,logo_text,color="#FFD700",fontsize=14,ha="center",va="center",fontweight="bold",zorder=10)

    # --- 7) Збереження ---
    fname = os.path.join(CACHE_DIR,"chart.png")
    fig.savefig(fname, dpi=150, bbox_inches='tight', facecolor="#222222")
    plt.close(fig)
    return fname

# ----------------- Генерація карти -----------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        date = data['date']          # yyyy-mm-dd
        time = data['time']          # HH:MM
        place = data['place']        # місто
        logo_text = data.get('logo_text','LOGO')
        logo_sign = data.get('logo_sign',None)

        dt_str = f"{date} {time}"
        dt_obj = dt.strptime(dt_str,"%Y-%m-%d %H:%M")

        geolocator = Nominatim(user_agent="astro_app")
        loc = geolocator.geocode(place)
        if loc is None:
            return jsonify({"error":"Invalid location"}),400
        tf = TimezoneFinder()
        tzname = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
        tz = pytz.timezone(tzname)
        dt_obj = tz.localize(dt_obj)

        chart = Chart(dt_obj, loc.latitude, loc.longitude, hsys='P')  # Placidus

        img_path = draw_natal_chart(chart,logo_text,logo_sign)

        response = {
            "image": f"/cache/{os.path.basename(img_path)}",
            "date": date,
            "time": time,
            "place": place
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "error": "Exception",
            "message": str(e),
            "trace": traceback.format_exc()
        }),500

# ----------------- Статика кешу -----------------
@app.route("/cache/<path:filename>")
def cached_file(filename):
    return send_from_directory(CACHE_DIR, filename)

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK",200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port, debug=True)