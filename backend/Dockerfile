# ====================== Базовий образ ======================
FROM python:3.12-slim

# ====================== Робоча директорія ======================
WORKDIR /app

# ====================== Встановлення системних пакетів ======================
RUN apt-get update && apt-get install -y \
    build-essential gcc libgeos-dev libfreetype6-dev libpng-dev libjpeg-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ====================== Встановлення Python-залежностей у venv ======================
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip wheel setuptools \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ====================== Копіюємо бекенд ======================
COPY . /app

# ====================== Створюємо директорію для ефемерид ======================
RUN mkdir -p /data/ephe

# ====================== Дозвіл на виконання entrypoint ======================
RUN chmod +x /app/entrypoint.sh

# ====================== Додаємо venv у PATH ======================
ENV PATH="/opt/venv/bin:$PATH"

# ====================== Тест залежностей (опційно) ======================
# RUN python /app/test_dependencies.py

# ====================== Безголовий режим matplotlib ======================
ENV MPLBACKEND="Agg"

# ====================== Відкритий порт ======================
EXPOSE 8080

# ====================== Entrypoint ======================
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:app", "--access-logfile", "-", "--error-logfile", "-"]