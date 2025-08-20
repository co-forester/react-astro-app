from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO

app = Flask(__name__)
CORS(app)

PLANETS = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
           const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]

ASPECTS = {
    'Conjunction': 0,
    'Sextile': 60,
    'Square': 90,
    'Trine': 120,
    'Opposition': 180
}

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.json
    date = data.get('date')      # 'YYYY-MM-DD'
    time = data.get('time')      # 'HH:MM'
    place = data.get('place')    # 'City'

    # Для прикладу використовуємо координати Києва
    geo = GeoPos(30.5234, 50.45)  

    dt = Datetime(f"{date} {time}", '+03:00')  # Твоя локальна зона
    chart = Chart(dt, geo, hsys=const.PLACIDUS)

    # Малюємо карту
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_xlim(-1.1,1.1)
    ax.set_ylim(-1.1,1.1)
    ax.axis('off')

    # Коло карти
    circle = plt.Circle((0,0), 1, fill=False, linewidth=2, color='black')
    ax.add_patch(circle)

    # Логотип у центрі
    ax.text(0, 0, 'Abireo Daria', fontsize=14, fontweight='bold',
            ha='center', va='center', color='purple')

    # Розташування планет на колі
    for planet in PLANETS:
        obj = chart.get(planet)
        angle = float(obj.lon) / 180 * 3.1416  # в радіанах
        x = 0.9 * plt.cos(angle)
        y = 0.9 * plt.sin(angle)
        ax.plot(x, y, 'o', markersize=12, label=planet)
        ax.text(x*1.05, y*1.05, planet, fontsize=10, ha='center', va='center')

    # Лінії аспектів (спрощено: тільки з’єднання)
    for i, p1 in enumerate(PLANETS):
        for j, p2 in enumerate(PLANETS):
            if j <= i: continue
            lon1 = float(chart.get(p1).lon)
            lon2 = float(chart.get(p2).lon)
            diff = abs(lon1 - lon2)
            for name, angle in ASPECTS.items():
                if abs(diff - angle) < 2:  # допуск 2 градуси
                    a1 = lon1/180*3.1416
                    a2 = lon2/180*3.1416
                    x1, y1 = 0.9*plt.cos(a1), 0.9*plt.sin(a1)
                    x2, y2 = 0.9*plt.cos(a2), 0.9*plt.sin(a2)
                    ax.plot([x1,x2], [y1,y2], linestyle='-', color='gray', alpha=0.5)

    # Зберігаємо у BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=True)
    buf.seek(0)
    plt.close(fig)

    # Відправка PNG як файл
    return send_file(buf, mimetype='image/png', download_name='chart.png')

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(port=8080)