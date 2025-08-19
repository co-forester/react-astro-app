#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import plotly.graph_objects as go
import math
import base64

app = Flask(__name__)
CORS(app)

# ====================== Планети ======================
PLANETS = [
    {"name": "Sun",     "radius": 0.50, "color": "yellow",     "angle": 0},
    {"name": "Moon",    "radius": 0.30, "color": "lightgray",  "angle": 45},
    {"name": "Mercury", "radius": 0.20, "color": "darkgray",   "angle": 90},
    {"name": "Venus",   "radius": 0.25, "color": "orange",     "angle": 135},
    {"name": "Mars",    "radius": 0.20, "color": "red",        "angle": 180},
    {"name": "Jupiter", "radius": 0.40, "color": "brown",      "angle": 225},
    {"name": "Saturn",  "radius": 0.35, "color": "goldenrod",  "angle": 270},
    {"name": "Uranus",  "radius": 0.30, "color": "lightblue",  "angle": 315},
]

LOGO_TEXT = "Albireo Daria"

# ====================== Health Check ======================
@app.get("/health")
def health():
    """
    Ендпоінт для Fly.io smoke checks
    """
    return jsonify({"status": "ok"}), 200

# ====================== Генерація карти ======================
@app.post("/generate")
def generate_chart():
    _ = request.get_json(silent=True) or {}
    fig = go.Figure()

    for planet in PLANETS:
        theta = list(range(0, 360, 5))
        r = [planet["radius"] * 4 for _ in theta]
        x = [r[i] * math.cos(math.radians(theta[i] + planet["angle"])) for i in range(len(theta))]
        y = [r[i] * math.sin(math.radians(theta[i] + planet["angle"])) for i in range(len(theta))]
        z = [0.1 * i for i in range(len(theta))]

        # Орбіти
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode="lines",
            line=dict(color=planet["color"], width=2),
            name=f'{planet["name"]} orbit',
            hoverinfo="skip"
        ))

        # Планети
        px = planet["radius"] * 4 * math.cos(math.radians(planet["angle"]))
        py = planet["radius"] * 4 * math.sin(math.radians(planet["angle"]))
        fig.add_trace(go.Scatter3d(
            x=[px], y=[py], z=[0],
            mode="markers+text",
            marker=dict(size=8, color=planet["color"], symbol="circle", line=dict(color="white", width=1)),
            text=[planet["name"]],
            textposition="top center",
            name=planet["name"]
        ))

    # Логотип
    logo_radius = 5.5
    logo_angle = 0
    lx = logo_radius * math.cos(math.radians(logo_angle))
    ly = logo_radius * math.sin(math.radians(logo_angle))
    fig.add_trace(go.Scatter3d(
        x=[lx], y=[ly], z=[0],
        mode="text",
        text=[LOGO_TEXT],
        textfont=dict(size=18),
        name="Logo",
        hoverinfo="skip"
    ))

    # Оформлення сцени
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="black",
            aspectmode="data"
        ),
        paper_bgcolor="black",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
    )

    # Експорт
    try:
        img_bytes = fig.to_image(format="png", width=800, height=800, scale=2, engine="kaleido")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        return jsonify({"chart_png": img_b64}), 200
    except Exception as e:
        # fallback на HTML, якщо PNG не згенеровано
        html = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False})
        return jsonify({"chart_html": html, "warning": f"png_export_failed: {str(e)}"}), 200

# ====================== Локальний запуск ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)