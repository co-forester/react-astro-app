FROM python:3.11-slim

WORKDIR /app

# Копіюємо файл залежностей та встановлюємо
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Додаємо каталог для ефемерид
RUN mkdir -p /data/ephe

# Завантажуємо ефемериди
RUN apt-get update && apt-get install -y git && \
    git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph && \
    apt-get remove -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Копіюємо весь проєкт
COPY . .

# Порт, на якому запускаємо Flask через Gunicorn
ENV PORT=8080

# Запуск через Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]