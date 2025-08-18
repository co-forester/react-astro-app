# app.py
from flask import Flask, request, jsonify
import plotly.graph_objects as go
import math
import io
import base64

app = Flask(__name__)

# Простий набір планет для прикладу
PLANETS = [
    {"name": "Sun", "radius": 0.5, "color": "yellow", "angle": 0},
    {"name": "Moon", "radius": 0.3, "color": "lightgray", "angle": 45},
    {"name": "Mercury", "radius": 0.2, "color": "darkgray", "angle": 90},
    {"name": "Venus", "radius": 0.25, "color": "orange", "angle": 135},
    {"name": "Mars", "radius": 0.2, "color": "red", "angle": 180},
    {"name": "Jupiter", "radius": 0.4, "color": "brown", "angle": 225},
    {"name": "Saturn", "radius": 0.35, "color": "goldenrod", "angle": 270},
    {"name": "Uranus", "radius": 0.3, "color": "lightblue", "angle": 315},
]

LOGO = "Albireo Daria"

@app.route("/generate", methods=["POST"])
def generate_chart():
    data = request.get_json()
    # date, time, place можна використовувати для розрахунків позицій планет (поки простий приклад)
    fig = go.Figure()

    # Створимо орбіти планет
    for planet in PLANETS:
        theta = [i for i in range(0, 360, 5)]
        r = [planet["radius"] * 4 for _ in theta]
        x = [r[i] * math.cos(math.radians(theta[i] + planet["angle"])) for i in range(len(theta))]
        y = [r[i] * math.sin(math.radians(theta[i] + planet["angle"])) for i in range(len(theta))]
        z = [0.1 * i for i in range(len(theta))]
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(color=planet["color"], width=2),
            name=f'{planet["name"]} orbit'
        ))
        # Додаємо планету як точку
        px = planet["radius"] * 4 * math.cos(math.radians(planet["angle"]))
        py = planet["radius"] * 4 * math.sin(math.radians(planet["angle"]))
        fig.add_trace(go.Scatter3d(
            x=[px], y=[py], z=[0],
            mode='markers+text',
            marker=dict(size=8, color=planet["color"], symbol='circle', line=dict(color='white', width=1)),
            text=[planet["name"]],
            textposition='top center',
            name=planet["name"]
        ))

    # Додаємо логотип на зовнішню орбіту
    logo_radius = 5.5
    logo_angle = 0
    lx = logo_radius * math.cos(math.radians(logo_angle))
    ly = logo_radius * math.sin(math.radians(logo_angle))
    fig.add_trace(go.Scatter3d(
        x=[lx], y=[ly], z=[0],
        mode='text',
        text=[LOGO],
        textfont=dict(size=18, color='white'),
        name='Logo'
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='black'
        ),
        paper_bgcolor='black',
        showlegend=False
    )

    # Експортуємо графік у PNG
    img_bytes = fig.to_image(format="png", width=800, height=800, scale=2)
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    return jsonify({"chart_png": img_b64})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)