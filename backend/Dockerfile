# Базовий образ
FROM python:3.10

# Робоча директорія
WORKDIR /app

# Копіюємо requirements
COPY requirements.txt ./

# Встановлюємо системні пакети для компіляції деяких бібліотек
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Додаємо каталог для ефемерид
RUN mkdir -p /data/ephe

# Завантаження ефемерид
RUN git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph

# Копіюємо весь код
COPY . .

# Порт
ENV PORT=8080

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]