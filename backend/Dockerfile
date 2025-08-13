# Використовуємо Python 3.10 для сумісності зі swisseph
FROM python:3.10-slim

# Встановлюємо необхідні системні пакети
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

# Копіюємо залежності
COPY requirements.txt ./

# Встановлюємо залежності Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо весь проект
COPY . .

# Запускаємо Flask через Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]