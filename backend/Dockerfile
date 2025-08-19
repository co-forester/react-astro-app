# ====================== Базовий образ ======================
FROM python:3.11-slim

# ====================== Робоча директорія ======================
WORKDIR /app

# ====================== Системні пакети ======================
RUN apt-get update && apt-get install -y \
    build-essential gcc libgeos-dev libfreetype6-dev libpng-dev libjpeg-dev \
    libffi-dev tar \
    && rm -rf /var/lib/apt/lists/*

# ====================== Python-залежності у venv ======================
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip wheel setuptools \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ====================== Копіюємо бекенд ======================
COPY . /app

# ====================== Директорія для ефемерид ======================
RUN mkdir -p /data/ephe

# ====================== Дозвіл на виконання entrypoint ======================
RUN chmod +x /app/entrypoint.sh

# ====================== Додаємо venv у PATH ======================
ENV PATH="/opt/venv/bin:$PATH"

# ====================== Безголовий matplotlib ======================
ENV MPLBACKEND="Agg"

# ====================== Порт ======================
EXPOSE 8080

# ====================== Entrypoint ======================
ENTRYPOINT ["/app/entrypoint.sh"]

# ====================== CMD Gunicorn ======================
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]