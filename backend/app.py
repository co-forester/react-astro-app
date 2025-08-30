# app.py — професійна натальна карта (Placidus), кеш PNG/JSON, дугові підписи, лого, DMS, ASC/MC/IC/DSC
import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# matplotlib — headless
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# ----------------- Ініціалізація -----------------
app = Flask(__name__)
CORS(app)

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL_DAYS = 30

geolocator = Nominatim(user_agent="albireo_astro_app")
tf = TimezoneFinder()

# ----------------- Конфіг -----------------
ZODIAC_SYMBOLS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
ZODIAC_NAMES   = ["Овен","Телець","Близнюки","Рак","Лев","Діва","Терези","Скорпіон",
                  "Стрілець","Козеріг","Водолій","Риби"]

# М’які пастельні: будинки
HOUSE_COLORS = [
    "#fde0dc", "#f8bbd0", "#e1bee7", "#d1c4e9",
    "#c5cae9", "#bbdefb", "#b3e5fc", "#b2ebf2",
    "#b2dfdb", "#c8e6c9", "#dcedc8", "#f0f4c3"
]

# Планети, символи, кольори
PLANET_SYMBOLS = {
    "Sun":"☉","Moon":"☽","Mercury":"☿","Venus":"♀","Mars":"♂",
    "Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇",
    "North Node":"☊","South Node":"☋","Ascendant":"ASC","MC":"MC",
    "Pars Fortuna":"⚶"
}
PLANET_COLORS = {
    "Sun":"#f6c90e","Moon":"#c0c0c0","Mercury":"#7d7d7d","Venus":"#e88fb4","Mars":"#e55d5d",
    "Jupiter":"#f3a33c","Saturn":"#b78b68","Uranus":"#69d2e7","Neptune":"#6a9bd1","Pluto":"#3d3d3d",
    "Ascendant":"#2ecc71","MC":"#8e44ad"
}

# Аспекти
ASPECTS_DEF = {
    "conjunction": {"angle": 0,   "orb": 8, "color": "#bbbbbb"},
    "sextile":     {"angle": 60,  "orb": 6, "color": "#a7d6a7"},
    "square":      {"angle": 90,  "orb": 6, "color": "#f3a7a7"},
    "trine":       {"angle": 120, "orb": 8, "color": "#9ec6f3"},
    "opposition":  {"angle": 180, "orb": 8, "color": "#8c2d3b"},
}

# ----------------- Утиліти -----------------
def cleanup_cache(days: int = CACHE_TTL_DAYS):
    now_ts = dt.now().timestamp()
    for fname in os.listdir(CACHE_DIR):
        fpath = os.path.join(CACHE_DIR, fname)
        try:
            if os.path.isfile(fpath):
                if now_ts - os.path.getmtime(fpath) > days * 24 * 3600:
                    os.remove(fpath)
        except Exception:
            pass

def cache_key(name, date_str, time_str, place):
    raw = f"{name}_{date_str}_{time_str}_{place}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def deg_to_dms(angle_float):
    angle = float(angle_float) % 360.0
    d = int(angle)
    m_f = (angle - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    if s == 60:
        s = 0; m += 1
    if m == 60:
        m = 0; d = (d + 1) % 360
    return f"{d}°{m}'{s}\""

def geocode_place(place, retries=2, timeout=10):
    for _ in range(retries + 1):
        try:
            loc = geolocator.geocode(place, timeout=timeout)
            if loc:
                return float(loc.latitude), float(loc.longitude)
            return None, None
        except GeocoderTimedOut:
            continue
        except Exception:
            break
    return None, None

def get_house_lon(chart, i):
    try: return chart.houses[i-1].lon
    except Exception: pass
    try: return chart.houses[i].lon
    except Exception: pass
    try: return chart.houses.get(i).lon
    except Exception: pass
    return None

# ----------------- Аспекти -----------------
def compute_aspects_manual(objects):
    results = []
    objs = [o for o in objects if getattr(o, "id", None) in PLANET_SYMBOLS]
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            p1, p2 = objs[i], objs[j]
            a1 = getattr(p1, "lon", 0) % 360
            a2 = getattr(p2, "lon", 0) % 360
            diff = abs(a1 - a2)
            if diff > 180: diff = 360 - diff
            for name, cfg in ASPECTS_DEF.items():
                if abs(diff - cfg["angle"]) <= cfg["orb"]:
                    results.append({
                        "planet1": getattr(p1, "id", str(p1)),
                        "planet1_symbol": PLANET_SYMBOLS.get(getattr(p1, "id", ""), ""),
                        "planet2": getattr(p2, "id", str(p2)),
                        "planet2_symbol": PLANET_SYMBOLS.get(getattr(p2, "id", ""), ""),
                        "type": name,
                        "angle": round(diff, 2),
                        "angle_dms": deg_to_dms(diff),
                        "color": cfg["color"]
                    })
                    break
    return results

# ----------------- Малювання карти -----------------
def draw_natal_chart(chart, aspects_list, save_path, name_for_center=None):
    fig = plt.figure(figsize=(12, 12))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.35)
    ax.set_xticks([]); ax.set_yticks([])
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    plt.rcParams["font.family"] = "DejaVu Sans"

    # --- Будинки (Placidus) ---
    try:
        for i in range(1, 13):
            cusp1 = get_house_lon(chart, i)
            cusp2 = get_house_lon(chart, (i % 12) + 1)
            if cusp1 is None or cusp2 is None: raise RuntimeError
            start_deg = cusp1 % 360
            end_deg   = cusp2 % 360
            if (end_deg - start_deg) <= 0: end_deg += 360
            theta_start, theta_end = np.deg2rad(start_deg), np.deg2rad(end_deg)
            ax.bar((theta_start+theta_end)/2, 1.10, abs(theta_end-theta_start), bottom=0,
                   color=HOUSE_COLORS[(i-1)%12], alpha=0.28, edgecolor="white", linewidth=0.6, zorder=0)
            ax.plot([np.deg2rad(start_deg), np.deg2rad(start_deg)], [0.15,1.18], color="#888888", lw=0.8, zorder=2)
    except Exception:
        pass

    # --- Зодіакальне кільце ---
    for i, sym in enumerate(ZODIAC_SYMBOLS):
        start = i * 30
        theta_start, theta_end = np.deg2rad(start), np.deg2rad(start+30)
        ax.bar((theta_start+theta_end)/2, 0.12, abs(theta_end-theta_start), bottom=1.18,
               color="#6a1b2c", edgecolor="white", linewidth=1.2, zorder=3)
        ax.plot([theta_start, theta_start], [1.18, 1.30], color="white", lw=1.2, zorder=4)

        center_deg = start + 15
        theta_c = np.deg2rad(center_deg)
        text_rot = -(center_deg)

        if sym == "♏":  # Скорпіон → Лого
            ax.text(theta_c, 1.225, "Albireo Daria^", fontsize=13, ha="center", va="center",
                    color="#FFD700", fontweight="bold", rotation=text_rot, rotation_mode="anchor", zorder=6)
        else:
            ax.text(theta_c, 1.205, sym, fontsize=20, ha="center", va="center",
                    color="white", fontweight="bold", rotation=text_rot, rotation_mode="anchor", zorder=5)
            ax.text(theta_c, 1.24, ZODIAC_NAMES[i], fontsize=9, ha="center", va="center",
                    color="white", rotation=text_rot, rotation_mode="anchor", zorder=5)

    # --- Центральне коло ---
    ax.add_artist(plt.Circle((0,0), 0.14, color="#f5f5f5", zorder=1, fill=True, ec="#dddddd", lw=0.5))
    ax.add_artist(plt.Circle((0,0), 0.10, color="#800000", zorder=10))
    if name_for_center:
        ax.text(0,0,name_for_center,color="white",ha="center",va="center",
                fontsize=10,fontweight="bold",zorder=11)

    # --- Номери домів ---
    try:
        for i in range(1,13):
            cusp1 = get_house_lon(chart,i)
            cusp2 = get_house_lon(chart,(i%12)+1)
            if cusp1 is None or cusp2 is None: raise RuntimeError
            diff=(cusp2-cusp1)%360; mid=(cusp1+diff/2)%360
            th_mid=np.deg2rad(mid)
            ax.text(th_mid,0.14,str(i),fontsize=9,ha="center",va="center",
                    color="#6a1b2c",fontweight="bold",zorder=7)
    except Exception:
        pass

    # --- Планети ---
    for obj in chart.objects:
        try:
            oid=getattr(obj,"id",None)
            if oid in PLANET_SYMBOLS:
                lon=obj.lon%360; th=np.deg2rad(lon); r=0.90
                sym=PLANET_SYMBOLS[oid]; col=PLANET_COLORS.get(oid,"black")
                ax.text(th,r,sym,fontsize=16,ha="center",va="center",color=col,zorder=8)
                ax.text(th,r-0.06,f"{oid} {deg_to_dms(obj.lon)}",fontsize=8,
                        ha="center",va="center",color=col,zorder=8)
        except: continue

    # --- Аспекти ---
    r_line=0.82
    for asp in aspects_list:
        try:
            p1=next(o for o in chart.objects if getattr(o,"id",None)==asp["planet1"])
            p2=next(o for o in chart.objects if getattr(o,"id",None)==asp["planet2"])
            th1,th2=np.deg2rad(p1.lon%360),np.deg2rad(p2.lon%360)
            d=((th2-th1+math.pi)%(2*math.pi))-math.pi
            steps=max(10,int(abs(d)/(math.pi/180)*2))
            thetas=np.linspace(th1,th1+d,steps); rs=np.full_like(thetas,r_line)
            ax.plot(thetas,rs,color=asp["color"],lw=1.4,alpha=0.95,zorder=5)
        except: continue

    plt.savefig(save_path,dpi=160,bbox_inches="tight",facecolor=fig.get_facecolor())
    plt.close(fig)

# ----------------- /generate -----------------
@app.route("/generate", methods=["POST"])
def generate():
    try:
        cleanup_cache()
        data=request.get_json() or {}
        name=data.get("name") or "Person"
        date_str=data.get("date"); time_str=data.get("time")
        place=data.get("place") or data.get("city")
        if not(date_str and time_str and place):
            return jsonify({"error":"Надішліть date (YYYY-MM-DD), time (HH:MM) та place"}),400

        key=cache_key(name,date_str,time_str,place)
        json_path=os.path.join(CACHE_DIR,f"{key}.json")
        png_path=os.path.join(CACHE_DIR,f"{key}.png")

        if os.path.exists(json_path) and os.path.exists(png_path):
            with open(json_path,"r",encoding="utf-8") as f: cached=json.load(f)
            base_url=request.host_url.rstrip("/")
            cached["chart_url"]=f"{base_url}/cache/{key}.png"
            return jsonify(cached)

        lat,lon=geocode_place(place)
        if lat is None: return jsonify({"error":"Місце не знайдено"}),400

        tz_str=tf.timezone_at(lat=lat,lng=lon) or "UTC"; tz=pytz.timezone(tz_str)
        naive=dt.strptime(f"{date_str} {time_str}","%Y-%m-%d %H:%M")
        local_dt=tz.localize(naive); offset_hours=local_dt.utcoffset().total_seconds()/3600.0
        fdate=Datetime(local_dt.strftime("%Y/%m/%d"),local_dt.strftime("%H:%M"),offset_hours)
        pos=GeoPos(lat,lon); chart=Chart(fdate,pos,hsys='P')

        aspects_json=compute_aspects_manual(chart.objects)
        draw_natal_chart(chart,aspects_json,png_path,name_for_center=name)

        base_url=request.host_url.rstrip("/")
        out={"name":name,"date":date_str,"time":time_str,"place":place,"timezone":tz_str,
             "aspects_json":aspects_json,"chart_url":f"{base_url}/cache/{key}.png"}
        with open(json_path,"w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
        return jsonify(out)

    except Exception as e:
        traceback.print_exc(); return jsonify({"error":str(e)}),500

@app.route("/cache/<path:filename>")
def cached_file(filename): return send_from_directory(CACHE_DIR,filename)

@app.route("/health")
def health(): return "OK",200

if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port,debug=True)