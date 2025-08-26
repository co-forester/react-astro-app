from flask import Flask, request, jsonify
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import matplotlib.pyplot as plt
import math
import os

app = Flask(__name__)
CORS(app)

def parse_datetime(date_str, time_str):
    try:
        year, month, day = map(int, date_str.split('-'))
        hour, minute = map(int, time_str.split(':'))
        return Datetime(year, month, day, hour, minute)
    except Exception as e:
        raise ValueError(f"Invalid date/time format: {str(e)}")

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({'error': f'Error parsing JSON: {str(e)}'}), 400

        try:
            first_name = data.get('firstName', '')
            last_name = data.get('lastName', '')
            date_str = data.get('date', '')
            time_str = data.get('time', '')
            place_str = data.get('place', '')
        except Exception as e:
            return jsonify({'error': f'Error extracting data fields: {str(e)}'}), 400

        try:
            cities = {
                "Mykolaiv, Ukraine": (46.9753, 31.9946)
            }
            if place_str not in cities:
                return jsonify({'error': 'Unknown place'}), 400
            lat, lon = cities[place_str]
        except Exception as e:
            return jsonify({'error': f'Error handling location: {str(e)}'}), 400

        try:
            dt = parse_datetime(date_str, time_str)
            pos = GeoPos(lat, lon)
        except Exception as e:
            return jsonify({'error': f'Error creating Datetime/GeoPos: {str(e)}'}), 400

        try:
            chart = Chart(dt, pos, hsys='Placidus')  # Placidus
        except Exception as e:
            return jsonify({'error': f'Error creating chart: {str(e)}'}), 500

        try:
            points = {}
            for obj in const.PLANETS:
                try:
                    points[obj] = {'lon': chart.get(obj).lon}
                except:
                    continue
        except Exception as e:
            return jsonify({'error': f'Error extracting planets: {str(e)}'}), 500

        try:
            asp_list = []
            for i, obj1 in enumerate(const.PLANETS):
                for obj2 in const.PLANETS[i+1:]:
                    try:
                        aspect = chart.aspect(obj1, obj2)
                        if aspect:
                            asp_list.append({'obj1': obj1, 'obj2': obj2, 'type': aspect.type})
                    except:
                        continue
        except Exception as e:
            return jsonify({'error': f'Error calculating aspects: {str(e)}'}), 500

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

            for p, info in points.items():
                if 'lon' in info:
                    rad = math.radians(info['lon'])
                    x = 0.9 * math.cos(rad)
                    y = 0.9 * math.sin(rad)
                    ax.plot(x, y, 'o', markersize=10, label=p)
                    ax.text(x*1.05, y*1.05, p, fontsize=9)

            for a in asp_list:
                obj1 = points.get(a['obj1'])
                obj2 = points.get(a['obj2'])
                if obj1 and 'lon' in obj1 and obj2 and 'lon' in obj2:
                    rad1 = math.radians(obj1['lon'])
                    rad2 = math.radians(obj2['lon'])
                    x1, y1 = 0.9*math.cos(rad1), 0.9*math.sin(rad1)
                    x2, y2 = 0.9*math.cos(rad2), 0.9*math.sin(rad2)
                    ax.plot([x1,x2],[y1,y2], linestyle='--', color='gray', linewidth=0.8)

            plt.savefig('chart.png', bbox_inches='tight', dpi=150)
            plt.close(fig)
        except Exception as e:
            return jsonify({'error': f'Error drawing chart: {str(e)}'}), 500

        return jsonify({
            'firstName': first_name,
            'lastName': last_name,
            'date': date_str,
            'time': time_str,
            'place': place_str,
            'planets': points,
            'aspects': asp_list,
            'chartImage': '/chart.png'
        })

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route("/health")
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)