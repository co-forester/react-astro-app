# Використовуємо Python 3.10 slim
FROM python:3.10-slim

# Встановлюємо системні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо requirements і встановлюємо залежності
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копіюємо весь backend
COPY . .

# Місце для ефемерид (зовнішній том Fly.io монтується сюди)
VOLUME /data/ephe
ENV EPHE_PATH=/data/ephe
ENV SWISSEPH_EPHE_PATH=$EPHE_PATH

# Завантажуємо ефемериди, якщо каталог порожній
RUN bash -c '\
    if [ ! -d "/data/ephe" ] || [ -z "$(ls -A /data/ephe)" ]; then \
        echo "Завантажуємо ефемериди..."; \
        git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
        mkdir -p /data/ephe && \
        cp -r /tmp/swisseph/ephe/. /data/ephe/ && \
        rm -rf /tmp/swisseph; \
    fi'

# Порт
EXPOSE 8080

# Запуск
CMD ["python", "app.py"]