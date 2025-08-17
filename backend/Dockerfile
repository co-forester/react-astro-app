# Базовий образ
FROM python:3.11-slim

# Робоча папка всередині контейнера
WORKDIR /app

# Системні пакети
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements
COPY requirements.txt .

# Віртуальне оточення
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Встановлюємо залежності
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо весь бекенд
COPY . /app

# Створюємо директорію для ефемерид
RUN mkdir -p /data/ephe && \
    tar -xzf /app/ephe.tar.gz -C /data/ephe

# Копіюємо і робимо виконуваним entrypoint
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Відкритий порт
EXPOSE 8080

# Запуск Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]