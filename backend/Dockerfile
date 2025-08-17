# Базовий образ з Python
FROM python:3.11-slim

# Оновлюємо систему і встановлюємо залежності для matplotlib
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо файли
COPY requirements.txt .
COPY . .

# Встановлюємо Python-залежності
RUN pip install --no-cache-dir -r requirements.txt

# Створюємо папку для ephemeris Flatlib
RUN mkdir -p /data/ephe

# Встановлюємо EPHE для Flatlib (Swiss Ephemeris)
# Завантажуємо актуальні ephemeris файли
RUN apt-get update && apt-get install -y wget unzip && \
    wget -O /tmp/seph.zip https://www.astro.com/ftp/swisseph/ephe/sepl_23.zip && \
    unzip /tmp/seph.zip -d /data/ephe && rm /tmp/seph.zip

# Відкриваємо порт
EXPOSE 8080

# Команда запуску
CMD ["python", "app.py"]