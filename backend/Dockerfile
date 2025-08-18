# ====================== Базовий образ ======================
FROM python:3.10.18-slim

# ====================== Робоча директорія ======================
WORKDIR /app

# ====================== Встановлення системних пакетів ======================
RUN apt-get update && apt-get install -y \
    build-essential gcc libgeos-dev libfreetype6-dev libpng-dev libjpeg-dev tar bash \
    && rm -rf /var/lib/apt/lists/*

# ====================== Встановлення Python-залежностей у venv ======================
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# ====================== Копіюємо бекенд ======================
COPY . /app

# ====================== Створюємо директорію для ефемерид ======================
RUN mkdir -p /data/ephe

# ====================== Дозвіл на виконання entrypoint ======================
RUN chmod +x /app/entrypoint.sh

# ====================== Додаємо venv у PATH ======================
ENV PATH="/opt/venv/bin:$PATH"

# ====================== Тест залежностей ======================
RUN /opt/venv/bin/python /app/test_dependencies.py

# ====================== Безголовий режим matplotlib ======================
ENV MPLBACKEND="Agg"

# ====================== Відкритий порт ======================
EXPOSE 8080

# ====================== Entrypoint ======================
ENTRYPOINT ["/app/entrypoint.sh"]