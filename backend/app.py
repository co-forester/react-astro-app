import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from matplotlib.text import TextPath
from matplotlib.transforms import Affine2D
from matplotlib import patheffects

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from flatlib.chart import Chart
from flatlib import const

# ------------------- Flask -------------------
app = Flask(__name__)
CORS(app)

# ------------------- Constants -------------------
ZODIAC_SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_COLORS = ['#FF6666','#FF9966','#FFCC66','#FFFF66','#99FF66','#66FF99','#66FFFF','#6699FF','#9966FF','#FF66FF','#FF6699','#FF3366']
ASPECTS = {'Conjunction': 0, 'Opposition': 180, 'Square': 90, 'Trine': 120, 'Sextile': 60}
PLANET_SYMBOLS = {'Sun':'☉','Moon':'☽','Mercury':'☿','Venus':'♀','Mars':'♂','Jupiter':'♃','Saturn':'♄','Uranus':'♅','Neptune':'♆','Pluto':'♇'}

# ------------------- Generate Chart -------------------
def draw_chart(chart):
    fig, ax = plt.subplots(figsize=(10,10))
    ax.set_xlim(-1.2,1.2)
    ax.set_ylim(-1.2,1.2)
    ax.axis('off')

    # Draw Zodiac arcs
    for i, sign in enumerate(ZODIAC_SIGNS):
        start = i*30
        wedge = Wedge(center=(0,0), r=1, theta1=start, theta2=start+30, facecolor=SIGN_COLORS[i], alpha=0.2)
        ax.add_patch(wedge)
        # Sign names along arc
        angle_rad = (start+15) * 3.14159/180
        x = 0.75 * np.cos(angle_rad)
        y = 0.75 * np.sin(angle_rad)
        ax.text(x, y, sign, ha='center', va='center', rotation=(start+15), rotation_mode='anchor', fontsize=12, fontweight='bold')

    # Draw houses as thin lines
    for h in range(12):
        angle = h*30
        x = [0, 1.0*np.cos(np.deg2rad(angle))]
        y = [0, 1.0*np.sin(np.deg2rad(angle))]
        ax.plot(x, y, color='gray', linewidth=1, alpha=0.5)

    # Draw planets
    for p in chart.planets:
        pos = chart.get(p).lon
        x = 0.85 * np.cos(np.deg2rad(pos))
        y = 0.85 * np.sin(np.deg2rad(pos))
        ax.text(x, y, PLANET_SYMBOLS.get(p,p), fontsize=14, fontweight='bold', ha='center', va='center')

    # Draw AC, DC, IC, VC
    angles = {'AC': chart.houses['1'].lon, 'DC': chart.houses['7'].lon,
              'IC': chart.houses['4'].lon, 'VC': chart.houses['10'].lon}
    for k,v in angles.items():
        x = 0.9*np.cos(np.deg2rad(v))
        y = 0.9*np.sin(np.deg2rad(v))
        ax.text(x, y, k, fontsize=12, fontweight='bold', color='red', ha='center', va='center')

    # Center logo
    ax.add_patch(Circle((0,0),0.1,color='black'))
    ax.text(0,0,'Serjio',color='white',ha='center',va='center',fontsize=10,fontweight='bold')

    # Save figure
    plt.savefig('chart.png', bbox_inches='tight', dpi=150)
    plt.close()

# ------------------- Routes -------------------
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    date = data['date']
    time = data['time']
    city = data['city']

    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(city)
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    tz = pytz.timezone(tz_str)

    chart = Chart(date + ' ' + time, location.latitude, location.longitude, tz_str)

    # Draw professional chart
    draw_chart(chart)

    # Prepare planet positions
    planets = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto']
    planet_positions = {p: chart.get(p).lon for p in planets}

    return jsonify({
        'planets': planet_positions,
        'chart_url': '/chart.png'
    })

@app.route('/chart.png')
def chart_image():
    return send_from_directory('.', 'chart.png')

# ----------------- Health -----------------
@app.route("/health")
def health():
    return "OK", 200

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
    