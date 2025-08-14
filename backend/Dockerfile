# --- Базовий образ ---
FROM python:3.10-slim

# --- Робоча директорія ---
WORKDIR /app

# --- Системні пакети для компіляції Python-бібліотек ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    wget \
    curl \
    libatlas-base-dev \
    gfortran \
    pkg-config \
    ca-certificates \
    locales \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Копіюємо файл залежностей ---
COPY requirements.txt ./

# --- Оновлюємо pip і встановлюємо залежності ---
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Каталог для ефемерид ---
RUN mkdir -p /data/ephe

# --- Завантажуємо ефемериди swisseph ---
RUN git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph

# --- Копіюємо весь код проєкту ---
COPY . .

# --- Порт ---
ENV PORT=8080

# --- Команда запуску ---
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]