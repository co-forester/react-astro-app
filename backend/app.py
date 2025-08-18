# (залишаємо попередні імпорти та налаштування)

def add_glowing_orbit(radius, color='white', points=72):
    theta = [2*math.pi*i/points for i in range(points+1)]
    x = [radius*math.cos(t) for t in theta]
    y = [radius*math.sin(t) for t in theta]
    z = [0]*len(theta)
    # Основна орбіта
    main_line = go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color=color, width=2), showlegend=False)
    # Світловий ореол (розсіяння)
    glow_lines = []
    for scale in [1.02, 1.04]:
        glow_lines.append(go.Scatter3d(
            x=[scale*xi for xi in x],
            y=[scale*yi for yi in y],
            z=z,
            mode='lines',
            line=dict(color=color, width=1, dash='dot'),
            opacity=0.15,
            showlegend=False
        ))
    return [main_line] + glow_lines

# В основній функції генерації кадрів додаємо орбіти зі світлом
for idx in range(len(planet_data)):
    radius = radius_base + idx*0.2
    orbit_traces = add_glowing_orbit(radius, color='lightblue')
    for trace in orbit_traces:
        fig.add_trace(trace)

# Для планет залишаємо функцію add_planet_with_depth з попереднього коду
# Логотип інтегруємо як легке світіння
lx = (radius_base + len(planet_data)*0.25) * math.cos(angle_shift)
ly = (radius_base + len(planet_data)*0.25) * math.sin(angle_shift)
logo_traces = add_planet_with_depth(lx, ly, logo_z, 'lightblue')
# Додаємо текст як м’яке світло
logo_traces[-1].text = ['Albireo Daria']
logo_traces[-1].mode = 'text+markers'
logo_traces[-1].textfont = dict(size=22, color='lightblue', family='Arial')
for t in logo_traces:
    frame_data.append(t)

# (решта коду залишаємо без змін: кадри, аспекти, updatemenus)