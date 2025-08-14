# Використовуємо Python 3.10 slim
FROM python:3.10-slim

# Встановлюємо системні пакети
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
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо requirements і встановлюємо залежності Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Попередньо завантажуємо ефемериди
RUN mkdir -p /usr/share/ephe \
    && git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph \
    && cp /tmp/swisseph/ephe/* /usr/share/ephe/ \
    && rm -rf /tmp/swisseph

# Копіюємо проект
COPY . .

# Стандартний запуск Gunicorn
EXPOSE 8080
CMD ["gunicorn", "--workers=1", "--threads=1", "--timeout=120", "-b", "0.0.0.0:8080", "app:app"]