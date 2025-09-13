# ====================== Базовий образ ======================
FROM python:3.11-bullseye

# ====================== Робоча директорія ======================
WORKDIR /app

# ====================== Системні пакети ======================
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ make \
    libgeos-dev libfreetype6-dev libpng-dev libjpeg-dev \
    libffi-dev tar curl wget \
    libgl1 libglib2.0-0 \
    libbz2-dev liblzma-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# ====================== Python-залежності ======================
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools \
    && pip install --no-cache-dir -r requirements.txt

# ====================== Копіюємо бекенд ======================
COPY . /app

# ====================== Директорія для ефемерид ======================
RUN mkdir -p /data/ephe

# ====================== Дозвіл на виконання entrypoint ======================
RUN chmod +x /app/entrypoint.sh

# ====================== Безголовий matplotlib ======================
ENV MPLBACKEND="Agg"

# ====================== Порт ======================
EXPOSE 8080

# ====================== Entrypoint ======================
ENTRYPOINT ["/app/entrypoint.sh"]

# ====================== CMD Gunicorn ======================
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120", "app:app"]