from flask import Flask, request, jsonify
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
CORS(app)

STATIC_DIR = 'static'
CHART_FILE = os.path.join(STATIC_DIR, 'chart.png')

# Переконайся, що папка static існує
os.makedirs(STATIC_DIR, exist_ok=True)

@app.route('/generate', methods=['POST'])
def generate_chart():
    data = request.get_json()
    date = data.get('date')  # формат YYYY-MM-DD
    time = data.get('time')  # формат HH:MM
    place = data.get('place')  # наприклад "Kyiv, Ukraine"

    if not date or not time or not place:
        return jsonify({'error': 'Введіть дату, час та місце'}), 400

    try:
        # Для простоти ставимо координати Києва, можна покращити геокодингом
        geo = GeoPos(50.4501, 30.5234)
        dt = Datetime(f'{date} {time}', '+03:00')  # timezone +3
        chart = Chart(dt, geo)

        # Малюємо просту схему планет
        fig, ax = plt.subplots(figsize=(6,6))
        ax.set_title('Натальна карта (спрощено)')
        ax.text(0.5, 0.5, 'Тут буде карта', ha='center', va='center', fontsize=14)
        ax.axis('off')
        plt.savefig(CHART_FILE)
        plt.close()

        return jsonify({'chart_image_url': f'/static/chart.png'}), 200

    except Exception as e:
        return jsonify({'error': 'Помилка генерації карти', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)