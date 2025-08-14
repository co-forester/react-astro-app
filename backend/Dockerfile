# Базовий образ Python 3.10 slim
FROM python:3.10-slim

# Робоча директорія
WORKDIR /app

# Копіюємо requirements
COPY requirements.txt ./

# Встановлюємо системні пакети для збірки Python-залежностей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Оновлюємо pip і встановлюємо Python-залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Додаємо каталог для ефемерид
RUN mkdir -p /data/ephe

# Завантаження ефемерид для swisseph
RUN git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph

# Копіюємо весь код додатку
COPY . .

# Порт для Fly.io
ENV PORT=8080

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]