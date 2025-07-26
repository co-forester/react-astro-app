FROM python:3.10.18-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    build-essential \
    libgeos-dev \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean

WORKDIR /app

COPY requirements.txt ./
RUN python -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install -r requirements.txt

COPY . .

# Gunicorn запускає Flask app:app на 8080
CMD ["/app/.venv/bin/gunicorn", "-b", "0.0.0.0:8080", "app:app"]