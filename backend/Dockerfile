# Вибираємо точну версію Python
FROM python:3.10.18-slim

# Робоча папка всередині контейнера
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

# Копіюємо requirements
COPY requirements.txt .

# Створюємо віртуальне оточення і встановлюємо залежності
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# Копіюємо весь бекенд
COPY . /app

# Створюємо директорію для ефемерид
RUN mkdir -p /data/ephe

# Робимо entrypoint виконуваним
RUN chmod +x /app/entrypoint.sh

# Додаємо venv в PATH
ENV PATH="/opt/venv/bin:$PATH"

# Встановлюємо змінну для matplotlib безголового режиму
ENV MPLBACKEND="Agg"

# Відкритий порт
EXPOSE 8080

# Entrypoint і запуск Gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]