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

# Робоча директорія
WORKDIR /app

# Створюємо директорію для даних ephe (volume)
RUN mkdir -p /data/ephe

# Копіюємо лише requirements.txt для кешування шарів
COPY requirements.txt /app/

# Оновлюємо pip і встановлюємо залежності **без venv**
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Перевіримо, що flatlib встановився
RUN pip show flatlib

# Копіюємо решту проєкту
COPY . /app

# Виставляємо порт для Flask
EXPOSE 5000

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]