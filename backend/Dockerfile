FROM python:3.10-slim

# Встановлення системних пакетів
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    wget \
    unzip \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіювання requirements і встановлення залежностей
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копіювання проекту
COPY . .

# Порт
EXPOSE 8080

# Запуск через Gunicorn (4 воркери, 2 потоки, таймаут 120с)
CMD ["gunicorn", "--workers=4", "--threads=2", "--timeout=120", "-b", "0.0.0.0:8080", "app:app"]