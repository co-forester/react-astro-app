# Базовий образ
FROM python:3.10-slim

# Робоча директорія
WORKDIR /app

# Копіюємо requirements
COPY requirements.txt ./

# Встановлюємо системні залежності та pip-залежності
RUN apt-get update && apt-get install -y git build-essential wget && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y git build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Додаємо каталог для ефемерид
RUN mkdir -p /data/ephe

# Завантаження ефемерид swisseph
RUN git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph

# Копіюємо весь код додатку
COPY . .

# Встановлюємо порт
ENV PORT=8080

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]