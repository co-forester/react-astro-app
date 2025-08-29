import os
import math
import hashlib
from datetime import datetime as dt, timedelta

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects

# ---------------- Flask ----------------
app = Flask(__name__)
CORS(app)

CHART_DIR = "charts"
if not os.path.exists(CHART_DIR):
    os.makedirs(CHART_DIR)

# ---------------- Helpers ----------------
def parse_date(date_str, time_str, tz_str):
    """Parse date+time with timezone into flatlib Datetime"""
    year, month, day = map(int, date_str.split("-"))
    hour, minute = map(int, time_str.split(":"))
    tz = pytz.timezone(tz_str)
    dt_local = tz.localize(dt(year, month, day, hour, minute))
    return Datetime(dt_local.strftime("%Y/%m/%d"), dt_local.strftime("%H:%M"), tz_str)

def generate_chart_filename(data):
    """Create hash from input to use as cache filename"""
    key = f"{data['date']}_{data['time']}_{data['location']}"
    return hashlib.md5(key.encode()).hexdigest() + ".png"

def draw_natal_chart(chart, filename):
    """Draw natal chart with houses, planets, aspects, labels, logo"""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    ax.set_facecolor("white")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_ylim(0, 1)

    # --- Houses (pastel sectors) ---
    house_colors = ["#fde2e4", "#e2f0cb", "#bee1e6", "#f1f7b5",
                    "#d7e3fc", "#fce2db", "#d6eadf", "#fff1e6",
                    "#e4c1f9", "#fcd5ce", "#caffbf", "#bdb2ff"]

    for i, cusp in enumerate(chart.houses):
        start = math.radians(cusp.lon)
        end = math.radians(chart.houses[(i+1) % 12].lon)
        ax.barh(1, end - start, left=start, height=0.5,
                color=house_colors[i], edgecolor="none")

    # --- Planets ---
    for obj in chart.objects:
        lon = math.radians(obj.lon)
        r = 0.75
        deg = int(obj.lon)
        minutes = int((obj.lon - deg) * 60)
        seconds = int(((obj.lon - deg) * 3600) % 60)
        label = f"{obj} {deg}°{minutes}'{seconds}\""
        ax.plot(lon, r, "o", color="black")
        ax.text(lon, r+0.05, label, ha="center", va="center", fontsize=8)

    # --- Aspects ---
    planet_names = [o for o in chart.objects if o in const.MAIN_PLANETS]
    asp_colors = {
        const.CONJUNCTION: "black",
        const.OPPOSITION: "red",
        const.TRINE: "green",
        const.SQUARE: "orange",
        const.SEXTILE: "blue"
    }
    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i+1:]:
            asp = aspects.getAspect(chart.get(p1), chart.get(p2))
            if asp:
                lon1 = math.radians(chart.get(p1).lon)
                lon2 = math.radians(chart.get(p2).lon)
                ax.plot([lon1, lon2], [0.75, 0.75],
                        color=asp_colors.get(asp.type, "gray"), lw=1)

    # --- Logo (center circle) ---
    ax.text(0, 0, "MyAstro\nLogo", ha="center", va="center",
            fontsize=12, weight="bold")

    plt.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ---------------- Routes ----------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    location_name = data["location"]
    date = data["date"]
    time = data["time"]

    # Geocoding
    geolocator = Nominatim(user_agent="astro_app")
    loc = geolocator.geocode(location_name)
    if not loc:
        return jsonify({"error": "Location not found"}), 400

    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
    if not tz_str:
        tz_str = "UTC"

    # Build filename for caching
    filename = generate_chart_filename(data)
    filepath = os.path.join(CHART_DIR, filename)

    # If already exists & <30 days old → return cached
    if os.path.exists(filepath):
        mtime = dt.fromtimestamp(os.path.getmtime(filepath))
        if dt.now() - mtime < timedelta(days=30):
            return jsonify({"chart_url": f"/charts/{filename}"})

    # New chart
    fdate = parse_date(date, time, tz_str)
    fpos = GeoPos(loc.latitude, loc.longitude)
    chart = Chart(fdate, fpos, hsys="PLACIDUS")

    draw_natal_chart(chart, filepath)

    return jsonify({"chart_url": f"/charts/{filename}"})

@app.route("/charts/<path:filename>")
def charts(filename):
    return send_from_directory(CHART_DIR, filename)


@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)