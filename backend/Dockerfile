# Базовий образ
FROM python:3.10-slim

# Робоча директорія
WORKDIR /app

# Копіюємо requirements
COPY requirements.txt ./

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Додаємо каталог для ефемерид
RUN mkdir -p /data/ephe

# Завантаження ефемерид
RUN apt-get update && apt-get install -y git && \
    git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph && \
    apt-get remove -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Копіюємо весь код
COPY . .

# Порт
ENV PORT=8080

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]