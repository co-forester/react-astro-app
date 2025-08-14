# Повний образ Python 3.10
FROM python:3.10

WORKDIR /app

# Оновлення системи та базові пакети
RUN apt-get update && apt-get install -y \
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

# Копіюємо requirements
COPY requirements.txt ./

# Встановлюємо Python-залежності
RUN pip install --no-cache-dir -r requirements.txt

# Створюємо каталог для ефемерид
RUN mkdir -p /data/ephe

# Завантаження ефемерид swisseph
RUN git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph

# Копіюємо код проєкту
COPY . .

ENV PORT=8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]