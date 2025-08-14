# Базовий образ Python
FROM python:3.9-slim

# Встановлюємо потрібні системні пакети для flatlib/pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gfortran python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Робоча папка
WORKDIR /app

# Копіюємо файл з залежностями
COPY requirements.txt /app/

# Створюємо віртуальне оточення та встановлюємо пакети
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код аплікації
COPY . /app

# Порт на якому слухає Flask через Gunicorn
EXPOSE 5000

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]