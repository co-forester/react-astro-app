# app.py — професійна натальна карта (Placidus), кеш PNG/JSON, дугові підписи, лого, DMS, ASC/MC/IC/DSC
import os
import math
import json
import hashlib
import traceback
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless рендер
import matplotlib.pyplot as plt
import numpy as np

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# --- Налаштування Flask ---
app = Flask(__name__)
CORS(app)

# --- Директорії ---
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

STATIC_DIR = 'static'
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# --- Константи для карти ---
ZODIAC_SYMBOLS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
ZODIAC_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
HOUSE_COLORS = [("#fde0dd","#a50f15"),("#fa9fb5","#7a0177"),("#fcbba1","#cb181d"),("#fee0d2","#67000d"),("#fdd0a2","#e6550d"),("#fee6ce","#a63603"),("#e5f5f9","#0868ac"),("#99d8c9","#006d2c"),("#ccece6","#238b45"),("#bae4bc","#00441b"),("#f0f0f0","#636363"),("#d9d9d9","#252525")]

# --- Утиліти ---

def hash_key(*args):
    key = '|'.join(map(str,args))
    return hashlib.md5(key.encode()).hexdigest()

def cache_path(key, ext='json'):
    return os.path.join(CACHE_DIR, f'{key}.{ext}')

# --- Конвертація градусів у радіани полярної системи ---
def to_theta(deg):
    return np.deg2rad((90 - deg) % 360.0)

# --- Отримати довготу дому ---
def get_house_lon(chart, house_number):
    try:
        return float(chart.houses[house_number].lon)
    except Exception:
        return None

# --- Основна функція генерації натальної карти ---
def generate_chart(name, date_str, time_str, place_name, logo_text='', logo_sign=''):
    try:
        # --- Геокодинг ---
        geo_key = hash_key(place_name)
        geo_cache_file = cache_path(geo_key, 'json')
        if os.path.exists(geo_cache_file):
            with open(geo_cache_file,'r') as f:
                geo_data = json.load(f)
        else:
            geolocator = Nominatim(user_agent="astro_app")
            location = geolocator.geocode(place_name)
            if not location:
                return None
            geo_data = {'lat': location.latitude, 'lon': location.longitude}
            with open(geo_cache_file,'w') as f:
                json.dump(geo_data,f)

        lat = geo_data['lat']
        lon = geo_data['lon']

        # --- Часова зона ---
        tzf = TimezoneFinder()
        tz_str = tzf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
        dt_obj = dt.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        dt_obj = tz.localize(dt_obj)

        # --- Створення об'єкта Flatlib ---
        fdt = Datetime(dt_obj.strftime('%Y/%m/%d'), dt_obj.strftime('%H:%M'), tz_str or 'UTC')
        pos = GeoPos(lat, lon)
        chart = Chart(fdt, pos, hsys='P')

        # --- Підготовка кеш ключа ---
        chart_key = hash_key(name, date_str, time_str, place_name)
        png_file = cache_path(chart_key, 'png')
        json_file = cache_path(chart_key, 'json')

        # --- Якщо кеш існує ---
        if os.path.exists(png_file) and os.path.exists(json_file):
            return {'png': png_file, 'json': json_file}

        # --- Малювання карти ---
        fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar':True})
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2.0)
        ax.set_ylim(0, 1.5)
        ax.axis('off')

        # --- 2) Роздільники домів ---
        r_inner = 0.15
        r_outer = 1.05
        for i in range(1, 13):
            cusp = get_house_lon(chart, i)
            if cusp is None:
                continue
            th = to_theta(cusp % 360.0)
            ax.plot([th, th], [r_inner, r_outer], color="#888888", lw=0.9, zorder=2)

        # --- 3) Номери домів ---
        house_number_radius = 0.19
        for i in range(1, 13):
            c1 = get_house_lon(chart, i)
            c2 = get_house_lon(chart, (i % 12) + 1)
            if c1 is None or c2 is None:
                continue
            start = float(c1) % 360.0
            end = float(c2) % 360.0
            span = (end - start) % 360.0
            mid = (start + span / 2.0) % 360.0
            ax.text(to_theta(mid), house_number_radius, str(i), fontsize=10, ha="center", va="center", color="#6a1b2c", fontweight="bold", zorder=7)

        # --- 4) Кільце зодіаку з символами та поділкою градусів ---
        ring_radius_start = 1.10
        ring_height = 0.20
        for i, sym in enumerate(ZODIAC_SYMBOLS):
            start = i * 30.0
            end = start + 30.0
            span = (end - start) % 360.0
            mid = (start + span/2.0) % 360.0

            center = to_theta(mid)
            width = np.deg2rad(span)

            ax.bar(x=center, height=ring_height, width=width, bottom=ring_radius_start,
                   color=HOUSE_COLORS[i % 12][0], edgecolor=HOUSE_COLORS[i % 12][1], linewidth=1.2, zorder=3, align='center')

            ax.plot([to_theta(start), to_theta(start)], [ring_radius_start, ring_radius_start + ring_height + 0.01], color="white", lw=1.2, zorder=4)

            symbol_r = ring_radius_start + ring_height - 0.02
            label_r = ring_radius_start + 0.05

            if ZODIAC_NAMES[i] == logo_sign:
                ax.text(center, label_r, logo_text, fontsize=12, ha="center", va="center",
                        color="#FFD700", fontweight="bold", rotation=mid + 90, rotation_mode="anchor", zorder=6)
            else:
                ax.text(center, symbol_r, sym, fontsize=18, ha="center", va="center",
                        color="#ffffff", fontweight="bold", rotation=mid + 90, rotation_mode="anchor", zorder=6)
                ax.text(center, label_r, ZODIAC_NAMES[i], fontsize=9, ha="center", va="center",
                        color="#ffffff", rotation=mid + 90, rotation_mode="anchor", zorder=5)

            for deg_mark in range(0, 31, 5):
                theta_deg = to_theta(start + deg_mark)
                r_start = ring_radius_start + 0.01
                r_end = ring_radius_start + (0.02 if deg_mark % 10 == 0 else 0.015)
                ax.plot([theta_deg, theta_deg], [r_start, r_end], color="#faf6f7", lw=1, zorder=2)

        # --- 5) Центральне коло і ім’я ---
        max_name_len = len(str(name)) if name else 0
        central_circle_radius = max(0.16, 0.08 + max_name_len * 0.012)
        theta_full = np.linspace(0, 2 * np.pi, 361)
        ax.fill_between(theta_full, 0, central_circle_radius, color="#e9c7cf", alpha=0.97, zorder=9)
        ax.plot(theta_full, [central_circle_radius]*len(theta_full), color="#a05c6a", lw=1.2, zorder=10)
        if name:
            fontsize = min(14, int(central_circle_radius*130))
            ax.text(0,0,name,color="#800000",ha="center",va="center",fontsize=fontsize,fontweight="bold", zorder=15, clip_on=False)

        # --- Зберегти PNG ---
        fig.savefig(png_file, dpi=150, bbox_inches='tight', facecolor='#2b2b2b')
        plt.close(fig)

        # --- Зберегти JSON ---
        chart_data = { 'houses': {i:get_house_lon(chart,i) for i in range(1,13)}, 'date': date_str, 'time': time_str, 'place': place_name }
        with open(json_file,'w') as f:
            json.dump(chart_data,f)

        return {'png': png_file, 'json': json_file}

    except Exception as e:
        traceback.print_exc()
        return None

# --- Flask ендпоінт ---
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    name = data.get('name','')
    date_str = data.get('date','')
    time_str = data.get('time','')
    place_name = data.get('place','')
    logo_text = data.get('logo_text','')
    logo_sign = data.get('logo_sign','')

    result = generate_chart(name, date_str, time_str, place_name, logo_text, logo_sign)
    if result is None:
        return jsonify({'error':'Chart generation failed'}), 500
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)