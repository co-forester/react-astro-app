# --- Базовий образ ---
FROM python:3.10-slim

# --- Робоча директорія ---
WORKDIR /app

# --- Системні пакети для збірки pyswisseph та matplotlib ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        wget \
        curl \
        libatlas-base-dev \
        gfortran \
        pkg-config \
        ca-certificates \
        locales && \
    rm -rf /var/lib/apt/lists/*

# Встановлюємо локаль для matplotlib
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# --- Копіюємо файл залежностей ---
COPY requirements.txt ./

# --- Встановлюємо Python-залежності ---
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Додаємо каталог для ефемерид ---
RUN mkdir -p /data/ephe

# --- Завантажуємо ефемериди swisseph ---
RUN git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph

# --- Копіюємо весь код проєкту ---
COPY . .

# --- Задаємо порт ---
ENV PORT=8080

# --- Команда запуску ---
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]