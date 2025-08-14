# Використовуємо Python 3.10 (сумісний зі swisseph)
FROM python:3.10-slim

# Встановлюємо системні пакети, потрібні для matplotlib, геолокації та компіляції
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо requirements і встановлюємо Python-залежності
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект
COPY . .

# Копіюємо ефемериди swisseph у контейнер
# (якщо вони є локально у папці ephe)
COPY ephe /app/ephe

# Експортуємо порт
EXPOSE 8080

# Запускаємо Flask через Gunicorn
CMD ["gunicorn", "--workers=4", "--threads=2", "--timeout=120", "-b", "0.0.0.0:8080", "app:app"]