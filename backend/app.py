import os
import math
import hashlib
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
import matplotlib.cm as cm
import numpy as np

import mplcursors  # для інтерактивності

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects

CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

app = Flask(__name__)
CORS(app)

def clear_old_cache():
    now = datetime.utcnow()
    for filename in os.listdir(CACHE_DIR):
        path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(path):
            filetime = datetime.utcfromtimestamp(os.path.getmtime(path))
            if now - filetime > timedelta(days=30):
                os.remove(path)

def get_cache_path(date, time, place, name):
    key = f"{date}_{time}_{place}_{name}"
    filename = hashlib.md5(key.encode()).hexdigest() + ".png"
    return os.path.join(CACHE_DIR, filename)

def get_coordinates(place):
    geolocator = Nominatim(user_agent="albireo")
    location = geolocator.geocode(place)
    if not location:
        raise ValueError("Не вдалося знайти місто")
    return location.latitude, location.longitude

def create_chart_image(dt, geo, name):
    fig, ax = plt.subplots(figsize=(10,10))
    ax.set_xlim(-1.2,1.2)
    ax.set_ylim(-1.2,1.2)
    ax.axis('off')

    # Красиві кольори секторів з градієнтом
    colors = cm.viridis(np.linspace(0,1,12))
    for i in range(12):
        start = i*30
        wedge = Wedge((0,0), 1.0, start, start+30, width=0.2, facecolor=colors[i], edgecolor='black', alpha=0.6)
        ax.add_patch(wedge)

        # Основні риски кожні 10°
        for j in range(0,30,10):
            angle = math.radians(start+j)
            x0, y0 = 0.8*math.cos(angle), 0.8*math.sin(angle)
            x1, y1 = 0.9*math.cos(angle), 0.9*math.sin(angle)
            ax.plot([x0,x1],[y0,y1], color='black', lw=0.8)
        # Дрібні риски кожні 5°
        for j in range(5,30,5):
            if j%10==0: continue
            angle = math.radians(start+j)
            x0, y0 = 0.85*math.cos(angle), 0.85*math.sin(angle)
            x1, y1 = 0.9*math.cos(angle), 0.9*math.sin(angle)
            ax.plot([x0,x1],[y0,y1], color='black', lw=0.5)

        # Знак зодіаку та логотип
        angle = math.radians(start + 15)
        x = 0.85 * math.cos(angle)
        y = 0.85 * math.sin(angle)
        sign_name = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон","Стрілець","Козеріг","Водолій","Риби"][i]
        if i==7:
            ax.text(x, y, "Albireo Daria^", ha='center', va='center', fontsize=12, fontweight='bold', rotation=start+15)
        else:
            ax.text(x, y, sign_name, ha='center', va='center', fontsize=10, rotation=start+15)

    # Домові підписи (1–12)
    for i in range(12):
        start = i*30
        angle = math.radians(start + 15)
        x = 0.6 * math.cos(angle)
        y = 0.6 * math.sin(angle)
        ax.text(x, y, f"Дом {i+1}", ha='center', va='center', fontsize=9, color='darkred', fontweight='bold')

    # Центральне коло з ім'ям
    center_circle = Circle((0,0), 0.2, color='maroon', alpha=0.7)
    ax.add_patch(center_circle)
    ax.text(0,0, name, ha='center', va='center', color='white', fontsize=12, fontweight='bold')

    # Планети та асценденти з кольоровими акцентами
    chart = Chart(dt, geo, hsys='P')
    planets = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto','Asc']
    colors_planets = ['gold','silver','orange','pink','red','blue','brown','cyan','purple','black','green']
    planet_points = []
    for idx, p in enumerate(planets):
        obj = chart.get(p)
        lon = math.radians(obj.lon)
        r = 0.7
        x = r * math.cos(lon)
        y = r * math.sin(lon)
        point = ax.plot(x, y, 'o', markersize=8, color=colors_planets[idx], label=p)[0]
        planet_points.append((point, f"{p}: {int(obj.lon)}°{int((obj.lon-int(obj.lon))*60)}'{int((((obj.lon-int(obj.lon))*60)%1)*60)}\""))
    
    # Аспекти
    aspect_colors = {'Conjunction':'red','Opposition':'blue','Trine':'green','Square':'orange','Sextile':'purple'}
    for a in aspects.MAJOR:
        p1 = chart.get(a[0])
        p2 = chart.get(a[1])
        type_ = a[2]
        x1 = 0.7 * math.cos(math.radians(p1.lon))
        y1 = 0.7 * math.sin(math.radians(p1.lon))
        x2 = 0.7 * math.cos(math.radians(p2.lon))
        y2 = 0.7 * math.sin(math.radians(p2.lon))
        color = aspect_colors.get(type_,'gray')
        ax.plot([x1,x2],[y1,y2], color=color, linewidth=1)

    # Інтерактивність
    cursor = mplcursors.cursor([p[0] for p in planet_points], hover=True)
    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.set_text(planet_points[sel.index][1])
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

    return fig

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json
    if not data or 'date' not in data or 'time' not in data or 'place' not in data or 'name' not in data:
        return jsonify({"error":"Надішліть date (YYYY-MM-DD), time (HH:MM), place (рядок) та name"}),400
    date = data['date']
    time_ = data['time']
    place = data['place']
    name = data['name']

    cache_path = get_cache_path(date,time_,place,name)
    clear_old_cache()
    if os.path.exists(cache_path):
        return send_file(cache_path, mimetype='image/png')

    try:
        lat, lon = get_coordinates(place)
    except ValueError as e:
        return jsonify({"error": str(e)}),400

    dt = Datetime(date, time_, '+00:00')  # UTC
    geo = GeoPos(lat, lon)
    fig = create_chart_image(dt, geo, name)
    fig.savefig(cache_path, dpi=150)
    plt.close(fig)

    return send_file(cache_path, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)