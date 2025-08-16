# Базовий образ Python 3.10
FROM python:3.10-slim

# Встановлюємо потрібні системні пакети для Flatlib / pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gfortran python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Робоча папка
WORKDIR /app

# Копіюємо файл з залежностями
COPY requirements.txt /app/

# Створюємо віртуальне оточення та додаємо в PATH
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Оновлюємо pip та встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо архів ефемерид і розпаковуємо його у персистентний том
COPY ephe.tar.gz /app/ephe.tar.gz
RUN mkdir -p /data/ephe && tar -xzf /app/ephe.tar.gz -C /data/ephe

# Копіюємо код аплікації
COPY . /app

# Порт, на якому слухає Flask через Gunicorn
EXPOSE 8080

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]