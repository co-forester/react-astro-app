import os
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)

# Кольори для планет і аспектів
PLANET_COLORS = {
    const.SUN: 'gold',
    const.MOON: 'silver',
    const.MERCURY: 'green',
    const.VENUS: 'pink',
    const.MARS: 'red',
    const.JUPITER: 'blue',
    const.SATURN: 'brown',
    const.URANUS: 'cyan',
    const.NEPTUNE: 'navy',
    const.PLUTO: 'purple'
}

ASPECT_COLORS = {
    'CONJ': 'red',
    'OPP': 'blue',
    'TRI': 'green',
    'SQR': 'orange',
    'SEX': 'purple'
}

# Кольори для 12 будинків
HOUSES_COLORS = [
    '#ffe0b2', '#ffcc80', '#ffb74d', '#ffa726',
    '#ff9800', '#fb8c00', '#f57c00', '#ef6c00',
    '#e65100', '#ffccbc', '#ffab91', '#ff8a65'
]

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.json
        date = data['date']
        time = data['time']
        place = data['place']

        # Широта та довгота (заглушка)
        lat, lon = 50.45, 30.52  # Київ
        dt = Datetime(f"{date} {time}", '+03:00')
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)

        # Створюємо фігуру
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis('off')

        # Додаємо кола для будинків
        for i in range(12):
            ax.add_patch(plt.Circle((0, 0), 1 - i*0.08, fill=True, color=HOUSES_COLORS[i], alpha=0.3))

        # Додаємо планети
        for obj in chart.objects:
            x = 0.7 * np.cos(np.radians(obj.lon))
            y = 0.7 * np.sin(np.radians(obj.lon))
            ax.text(x, y, obj.id, color=PLANET_COLORS.get(obj.id, 'black'), fontsize=12, fontweight='bold')

        # Аспекти
        for asp in aspects.getAspects(chart):
            p1 = chart.get(asp.p1)
            p2 = chart.get(asp.p2)
            x1 = 0.7 * np.cos(np.radians(p1.lon))
            y1 = 0.7 * np.sin(np.radians(p1.lon))
            x2 = 0.7 * np.cos(np.radians(p2.lon))
            y2 = 0.7 * np.sin(np.radians(p2.lon))
            ax.plot([x1, x2], [y1, y2], color=ASPECT_COLORS.get(asp.type, 'grey'), linewidth=1.2)

        chart_path = "chart.png"
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close(fig)

        # HTML таблиця аспектів
        aspects_table = "<table><tr><th>Планета 1</th><th>Аспект</th><th>Планета 2</th><th>Градус</th></tr>"
        for asp in aspects.getAspects(chart):
            aspects_table += f"<tr style='color:{ASPECT_COLORS.get(asp.type,'black')}'><td>{asp.p1}</td><td>{asp.type}</td><td>{asp.p2}</td><td>{asp.orb:.1f}</td></tr>"
        aspects_table += "</table>"

        return jsonify({
            "chart_image_url": f"/chart.png",
            "aspects_table_html": aspects_table
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chart.png')
def chart_image():
    return send_file("chart.png", mimetype='image/png')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)