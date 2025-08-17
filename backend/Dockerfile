# Базовий образ Python 3.10
FROM python:3.10-slim

# Встановлюємо системні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gfortran python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Робоча папка
WORKDIR /app

# Копіюємо requirements
COPY backend/requirements.txt .

# Віртуальне оточення
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Встановлюємо залежності
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Копіюємо код і архів ефемерид
COPY backend/ /app/
COPY backend/ephe.tar.gz /app/

# Копіюємо entrypoint
COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Порт для Gunicorn
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]