# Базовий образ з Python 3.9
FROM python:3.9-slim

# Оновлення та встановлення необхідних системних пакетів
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    gfortran \
    pkg-config \
    ca-certificates \
    locales \
    python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо файли проєкту
COPY . /app

# Створюємо та активуємо virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Оновлюємо pip і встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Виставляємо порт для Flask
EXPOSE 5000

# Команда для запуску
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]