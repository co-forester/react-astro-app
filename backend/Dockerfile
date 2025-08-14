# --- базовий образ з Python 3.9 ---
FROM python:3.9-slim

# --- встановлюємо системні залежності ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    libatlas-base-dev \
    gfortran \
    pkg-config \
    ca-certificates \
    locales \
    python3-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# --- робоча директорія ---
WORKDIR /app

# --- копіюємо файли ---
COPY requirements.txt .
COPY . .

# --- оновлюємо pip і встановлюємо залежності ---
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# --- expose порт для Fly.io ---
EXPOSE 8080

# --- команда запуску додатку ---
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]