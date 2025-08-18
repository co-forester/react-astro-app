from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math
import os

app = Flask(__name__)
CORS(app)

CHART_FILE = 'chart.png'

# Координати міст
cities = {
    "Миколаїв, Україна": GeoPos(46.975, 31.994)
}

# Кольори для знаків зодіаку
zodiac_colors = [
    "#FF6666", "#FFCC66", "#FFFF66", "#66FF66", "#66FFFF", "#6699FF",
    "#CC66FF", "#FF66CC", "#FF9966", "#FF9966", "#99FF66", "#66FF99"
]

# Аспекти (угли) в градусах і кольори
aspects = {
    "Conjunction": ("#000000", 0),
    "Opposition": ("#FF0000", 180),
    "Square": ("#FFA500", 90),
    "Trine": ("#008000", 120),
    "Sextile": ("#0000FF", 60)
}

zodiac_signs = [
    "Овен", "Телець", "Близнюки", "Рак", "Лев", "Діва",
    "Терези", "Скорпіон", "Стрілець", "Козеріг", "Водолій", "Риби"
]

def generate_chart(date, time, place):
    if place not in cities:
        raise ValueError("Місце не знайдено")

    dt = Datetime(date, time, '+03:00')  # UTC+3
    geo = cities[place]
    chart = Chart(dt, geo)

    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')

    # Малюємо сектори зодіаку
    for i in range(12):
        start_angle = 2*math.pi*i/12
        end_angle = 2*math.pi*(i+1)/12
        ax.fill_between(
            [0, math.cos(start_angle), math.cos(end_angle)],
            [0, math.sin(start_angle), math.sin(end_angle)],
            color=zodiac_colors[i], alpha=0.2
        )
        mid_angle = (start_angle + end_angle)/2
        ax.text(1.05*math.cos(mid_angle), 1.05*math.sin(mid_angle),
                zodiac_signs[i], ha='center', va='center', fontsize=10, fontweight='bold')

    # Планети
    planet_names = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
        const.N_NODE, const.S_NODE, const.LILITH
    ]

    planet_positions = {}
    for pname in planet_names:
        try:
            p = chart.get(pname)
            angle = math.radians(p.lon)
            r = 0.8
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            planet_positions[pname] = (x, y, p.lon, p.sign)
            sign_index = zodiac_signs.index(p.sign) if p.sign in zodiac_signs else 0
            ax.plot(x, y, 'o', markersize=10, color=zodiac_colors[sign_index])
            ax.text(x*1.1, y*1.1, f"{pname} {p.sign} {p.lon:.1f}°", fontsize=8)
        except:
            continue

    # Лінії аспектів
    for i, p1 in enumerate(planet_names):
        for j in range(i+1, len(planet_names)):
            p2 = planet_names[j]
            if p1 in planet_positions and p2 in planet_positions:
                lon1 = planet_positions[p1][2]
                lon2 = planet_positions[p2][2]
                diff = abs(lon1 - lon2)
                for asp, (color, angle) in aspects.items():
                    if abs(diff - angle) <= 5:  # допуск ±5°
                        x1, y1 = planet_positions[p1][0], planet_positions[p1][1]
                        x2, y2 = planet_positions[p2][0], planet_positions[p2][1]
                        ax.plot([x1, x2], [y1, y2], '-', color=color, alpha=0.5)

    # Легенда аспектів
    legend_patches = [mpatches.Patch(color=color, label=f"{asp} ({angle}°)") for asp, (color, angle) in aspects.items()]
    ax.legend(handles=legend_patches, loc='upper right', fontsize=8)

    # Легенда знаків прямо на колі
    for i, sign in enumerate(zodiac_signs):
        angle = math.radians(i*30 + 15)  # центр знаку
        ax.text(1.3*math.cos(angle), 1.3*math.sin(angle), f"{sign}", fontsize=9,
                color=zodiac_colors[i], fontweight='bold', ha='center', va='center')

    ax.set_title(f"Натальна карта: {date} {time}\n{place}", fontsize=12, fontweight='bold')
    plt.savefig(CHART_FILE, bbox_inches='tight')
    plt.close()

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        date = data['date']
        time = data['time']
        place = data['place']

        generate_chart(date, time, place)

        return jsonify({
            "message": "Chart generated successfully",
            "chart_url": f"/{CHART_FILE}"
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "trace": repr(e)
        }), 400

@app.route(f'/{CHART_FILE}', methods=['GET'])
def get_chart():
    if os.path.exists(CHART_FILE):
        return send_file(CHART_FILE, mimetype='image/png')
    return jsonify({"error": "Chart not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)