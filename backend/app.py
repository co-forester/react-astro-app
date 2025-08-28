import os
import math
import json
from datetime import datetime as dt, timedelta
from hashlib import md5

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects

app = Flask(__name__)
CORS(app)

geolocator = Nominatim(user_agent="astro_app")
tf = TimezoneFinder()

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

ASPECT_COLORS = {
    "conjunction": "#ccc",
    "sextile": "#f7eaea",
    "square": "#8b8b8b",
    "trine": "#d4a5a5",
    "opposition": "#4a0f1f"
}

PLANET_COLORS = {
    "Sun": "#FFD700",
    "Moon": "#C0C0C0",
    "Mercury": "#8B0000",
    "Venus": "#FF69B4",
    "Mars": "#FF4500",
    "Jupiter": "#1E90FF",
    "Saturn": "#800080",
    "Uranus": "#00CED1",
    "Neptune": "#0000FF",
    "Pluto": "#A52A2A",
    "North Node": "#00FF00",
    "South Node": "#FF6347"
}

ZODIAC_SIGNS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]

def cache_key(name, date, time, place):
    key_str = f"{name}|{date}|{time}|{place}"
    return md5(key_str.encode()).hexdigest()

def cleanup_cache(days=30):
    now = dt.now()
    for f in os.listdir(CACHE_DIR):
        path = os.path.join(CACHE_DIR, f)
        if os.path.isfile(path):
            if now - dt.fromtimestamp(os.path.getmtime(path)) > timedelta(days=days):
                os.remove(path)

def compute_aspects(chart):
    aspect_list = []
    aspect_types = {
        const.CONJUNCTION: "conjunction",
        const.SEXTILE: "sextile",
        const.SQUARE: "square",
        const.TRINE: "trine",
        const.OPPOSITION: "opposition"
    }
    objs = chart.objects
    for i, p1 in enumerate(objs):
        for j, p2 in enumerate(objs):
            if i >= j:
                continue
            asp = aspects.getAspect(p1, p2, 6)
            if asp and asp.type in aspect_types:
                type_str = aspect_types[asp.type]
                aspect_list.append({
                    "planet1": p1.id,
                    "planet2": p2.id,
                    "planet1_symbol": p1.symbol,
                    "planet2_symbol": p2.symbol,
                    "type": type_str,
                    "color": ASPECT_COLORS.get(type_str, "#ccc"),
                    "angle": round(asp.angle,2)
                })
    return aspect_list

def draw_natal_chart(chart, aspects_list, name="Person", save_path="static/chart.png"):
    fig, ax = plt.subplots(figsize=(12,12))
    ax.axis("off")
    
    # Зодіакальні сектори
    for i, sign in enumerate(ZODIAC_SIGNS):
        start_angle = i * 30
        wedge = Wedge((0,0),1,start_angle,start_angle+30,facecolor="#f0e6e6",edgecolor="white",lw=1)
        ax.add_artist(wedge)
        angle_rad = math.radians(start_angle + 15)
        ax.text(1.05*math.cos(angle_rad),1.05*math.sin(angle_rad),sign,color="white",
                fontsize=18,ha="center",va="center")
    
    # Домів сектора
    for i, cusp in enumerate(chart.cusps):
        start = cusp
        next_cusp = chart.cusps[i+1] if i+1<12 else chart.cusps[0]
        angle_rad = math.radians((start + next_cusp)/2)
        ax.text(0.7*math.cos(angle_rad),0.7*math.sin(angle_rad),str(i+1),
                fontsize=14,ha="center",va="center",color="#4a0f1f")
    
    # Логотип у секторі Скорпіона (знак 7)
    sc_angle = 180+15
    ax.text(1.15*math.cos(math.radians(sc_angle)),1.15*math.sin(math.radians(sc_angle)),
            "Albireo Daria", color="white", fontsize=14, ha="center", va="center", rotation=0)
    
    # Планети
    for obj in chart.objects:
        angle_rad = math.radians(obj.lon)
        x = 0.85 * math.cos(angle_rad)
        y = 0.85 * math.sin(angle_rad)
        ax.plot(x,y,"o",color=PLANET_COLORS.get(obj.id,"#6a1b2c"),markersize=12)
        ax.text(x*1.05,y*1.05,obj.symbol,fontsize=14,ha="center",va="center",color="white")
    
    # Аспекти
    for asp in aspects_list:
        p1 = next(o for o in chart.objects if o.id==asp["planet1"])
        p2 = next(o for o in chart.objects if o.id==asp["planet2"])
        x1 = 0.85*math.cos(math.radians(p1.lon))
        y1 = 0.85*math.sin(math.radians(p1.lon))
        x2 = 0.85*math.cos(math.radians(p2.lon))
        y2 = 0.85*math.sin(math.radians(p2.lon))
        ax.plot([x1,x2],[y1,y2],color=asp["color"],lw=1)
    
    plt.savefig(save_path,dpi=150,bbox_inches="tight")
    plt.close(fig)

@app.route("/generate",methods=["POST"])
def generate_chart():
    try:
        data = request.get_json()
        name = data["name"]
        date_str = data["date"]
        time_str = data["time"]
        place = data["place"]
        
        key = cache_key(name,date_str,time_str,place)
        chart_path = os.path.join(CACHE_DIR,f"{key}.png")
        cache_path = os.path.join(CACHE_DIR,f"{key}.json")
        
        cleanup_cache()
        
        if os.path.exists(cache_path):
            with open(cache_path,"r") as f:
                cache_data = json.load(f)
            return jsonify(cache_data)
        
        loc = geolocator.geocode(place)
        tz_str = tf.timezone_at(lat=loc.latitude,lon=loc.longitude)
        tz = pytz.timezone(tz_str)
        dt_obj = dt.strptime(f"{date_str} {time_str}","%Y-%m-%d %H:%M")
        dt_obj = tz.localize(dt_obj)
        
        flat_dt = Datetime(dt_obj.year,dt_obj.month,dt_obj.day,dt_obj.hour,dt_obj.minute,dt_obj.second, tz_str)
        geo = GeoPos(loc.latitude,loc.longitude)
        chart = Chart(flat_dt,geo,const.PLACIDUS)
        
        aspect_list = compute_aspects(chart)
        draw_natal_chart(chart,aspect_list,name=name,save_path=chart_path)
        
        cache_data = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "timezone": tz_str,
            "chart_url": f"/cache/{key}.png",
            "aspects_json": aspect_list
        }
        with open(cache_path,"w") as f:
            json.dump(cache_data,f)
        return jsonify(cache_data)
        
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/cache/<filename>")
def get_cached_chart(filename):
    return send_from_directory(CACHE_DIR,filename)

@app.route("/health")
def health():
    return "OK",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080)