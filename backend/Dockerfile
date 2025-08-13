FROM python:3.10-slim

# Системні пакети
RUN apt-get update && apt-get install -y \
    build-essential \
    libgeos-dev \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо залежності
COPY requirements.txt ./

# Встановлюємо Python пакети
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# Копіюємо весь код
COPY . .

# Запуск бекенду через Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]