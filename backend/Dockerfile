FROM python:3.10.18-slim

WORKDIR /app

# Встановлюємо системні пакети
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libgeos-dev \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements і встановлюємо залежності у venv
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# Копіюємо весь бекенд
COPY . /app

# Створюємо директорію для ефемерид
RUN mkdir -p /data/ephe

# Дозвіл на виконання entrypoint
RUN chmod +x /app/entrypoint.sh

# Додаємо venv у PATH
ENV PATH="/opt/venv/bin:$PATH"

# Встановлюємо безголовий режим matplotlib
ENV MPLBACKEND="Agg"

# Відкритий порт для Gunicorn
EXPOSE 8080

# Змінна середовища для Fly / динамічний порт
ENV PORT=8080

# Entrypoint і запуск Gunicorn через entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
# CMD можна залишити пустим — entrypoint сам стартує Gunicorn на PORT
CMD []