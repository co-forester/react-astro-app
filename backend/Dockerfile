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
    libc-dev \
    libgfortran5 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Директорія для volume Fly.io
RUN mkdir -p /data/ephe

# Копіюємо лише requirements.txt для кешування шару
COPY requirements.txt /app/

# Створюємо virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Оновлюємо pip і встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту проєкту
COPY . /app

# Виставляємо порт Flask
EXPOSE 5000

# Запуск Gunicorn із virtualenv
CMD ["/opt/venv/bin/gunicorn", "-b", "0.0.0.0:5000", "app:app"]