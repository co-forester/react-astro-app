from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.object import DEFAULT_IDS

print("✅ Flatlib успішно імпортовано!")

# Створюємо тестову натальну карту
date = '2000-01-01'
time = '12:00'
pos = GeoPos('50.45', '30.52')  # Київ
dt = Datetime(date, time, '+03:00')
chart = Chart(dt, pos)

print("🪐 Об’єкти карти:")
for obj in chart.objects:
    print(f"{obj.id}: {obj.sign} {obj.lon}")