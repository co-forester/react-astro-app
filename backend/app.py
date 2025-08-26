from flask import Flask, request, jsonify
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import matplotlib.pyplot as plt
import math
import os
import logging

app = Flask(__name__)
CORS(app)

def create_datetime(date_str: str, time_str: str):
    try:
        day, month, year = map(int, date_str.split('.'))
        hour, minute = map(int, time_str.split(':'))
        dt = Datetime(year, month, day, hour, minute, zone='+3')
        return dt
    except Exception as e:
        raise ValueError(f"Error creating Datetime: {str(e)}")

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        data = request.get_json()
        logging.info("Received JSON data successfully")
    except Exception as e:
        logging.error(f"Error parsing JSON: {str(e)}")
        return jsonify({'error': f'Error parsing JSON: {str(e)}'}), 400

    first_name = data.get('firstName', '')
    last_name = data.get('lastName', '')
    date_str = data.get('date', '')
    time_str = data.get('time', '')
    place_str = data.get('place', '')

    try:
        # Простий geocoding через словник міст з нормалізацією
        cities = {
            "Mykolaiv, Ukraine": (46.9753, 31.9946)
        }
        place_str_normalized = place_str.strip().lower()
        cities_normalized = {k.lower(): v for k, v in cities.items()}

        if place_str_normalized not in cities_normalized:
            logging.error("Unknown place: " + place_str)
            return jsonify({'error': 'Unknown place'}), 400

        lat, lon = cities_normalized[place_str_normalized]
        pos = GeoPos(lat, lon)
        logging.info(f"Created GeoPos for place {place_str}: lat={lat}, lon={lon}")
    except Exception as e:
        logging.error(f"Error creating GeoPos: {str(e)}")
        return jsonify({'error': f'Error creating GeoPos: {str(e)}'}), 500

    try:
        dt = create_datetime(date_str, time_str)
    except Exception as e:
        logging.error(f"Error creating Datetime: {str(e)}")
        return jsonify({'error': f'Error creating Datetime: {str(e)}'}), 500

    try:
        chart = Chart(dt, pos, hsys='Placidus')
        logging.info("Chart object created successfully")
    except Exception as e:
        logging.error(f"Error creating Chart object: {str(e)}")
        return jsonify({'error': f'Error creating Chart object: {str(e)}'}), 500

    # Збираємо позиції планет
    points = {}
    for obj in const.PLANETS:
        try:
            points[obj] = {'lon': chart.get(obj).lon}
        except Exception:
            continue
    logging.info(f"Collected planet positions: {points}")

    # Створюємо список аспектів
    asp_list = []
    for i, obj1 in enumerate(const.PLANETS):
        for obj2 in const.PLANETS[i+1:]:
            try:
                aspect = chart.aspect(obj1, obj2)
                if aspect:
                    asp_list.append({'obj1': obj1, 'obj2': obj2, 'type': aspect.type})
            except Exception:
                continue
    logging.info(f"Collected aspects list: {asp_list}")

    # Малюємо натальну карту
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.axis('off')

        SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        colors = ['#FF9999','#FFCC99','#FFFF99','#CCFF99','#99FF99','#99FFFF',
                  '#99CCFF','#9999FF','#CC99FF','#FF99FF','#FF99CC','#FF6666']

        for i, sign in enumerate(SIGNS):
            angle = i * 30
            rad = math.radians(angle)
            x = 1.1 * math.cos(rad)
            y = 1.1 * math.sin(rad)
            ax.text(x, y, sign, ha='center', va='center', color=colors[i], fontsize=10, fontweight='bold')

        # Планети на колі
        for p, info in points.items():
            try:
                rad = math.radians(info['lon'])
                x = 0.9 * math.cos(rad)
                y = 0.9 * math.sin(rad)
                ax.plot(x, y, 'o', markersize=10, label=p)
                ax.text(x*1.05, y*1.05, p, fontsize=9)
            except Exception:
                continue

        # Аспекти лініями
        for a in asp_list:
            try:
                obj1 = points.get(a['obj1'])
                obj2 = points.get(a['obj2'])
                if obj1 and 'lon' in obj1 and obj2 and 'lon' in obj2:
                    rad1 = math.radians(obj1['lon'])
                    rad2 = math.radians(obj2['lon'])
                    x1, y1 = 0.9*math.cos(rad1), 0.9*math.sin(rad1)
                    x2, y2 = 0.9*math.cos(rad2), 0.9*math.sin(rad2)
                    ax.plot([x1,x2],[y1,y2], linestyle='--', color='gray', linewidth=0.8)
            except Exception:
                continue

        plt.savefig('chart.png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        logging.info("Chart image saved as chart.png")
    except Exception as e:
        logging.error(f"Error drawing chart: {str(e)}")
        return jsonify({'error': f'Error drawing chart: {str(e)}'}), 500

    return jsonify({
        'firstName': first_name,
        'lastName': last_name,
        'date': date_str,
        'time': time_str,
        'place': place_str,
        'planets': points,
        'aspects': asp_list,
        'chart_image_url': '/chart.png'
    })

@app.route("/health")
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)