# Базовий образ Python
FROM python:3.10-slim

# Встановлюємо системні пакети для збірки flatlib/pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gfortran python3-dev libc6-dev gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Робоча папка
WORKDIR /app

# Копіюємо файл з залежностями
COPY requirements.txt /app/

# Створюємо віртуальне оточення та додаємо його в PATH
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Оновлюємо pip і встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код аплікації
COPY . /app

# Створюємо директорію для ефемерид (Fly.io mount)
VOLUME ["/data/ephe"]
ENV EPHE_PATH="/data/ephe"

# Порт на якому слухає Flask через Gunicorn
EXPOSE 8080

# Команда запуску через Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]