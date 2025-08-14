# --- Базовий образ ---
FROM python:3.10-slim

# --- Робоча директорія ---
WORKDIR /app

# --- Копіюємо dependencies ---
COPY requirements.txt ./

# --- Встановлюємо залежності ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Створюємо каталог для ефемерид ---
RUN mkdir -p /data/ephe

# --- Завантаження ефемерид ---
RUN apt-get update && apt-get install -y git && \
    git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cp -r /tmp/swisseph/ephe/* /data/ephe/ && \
    rm -rf /tmp/swisseph && \
    apt-get remove -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# --- Копіюємо код додатку ---
COPY . .

# --- Порт додатку ---
ENV PORT=8080

# --- Команда запуску через Gunicorn ---
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]