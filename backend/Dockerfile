# Використовуємо Python 3.10
FROM python:3.10-slim

# Встановлюємо системні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    wget \
    unzip \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо та встановлюємо залежності Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект
COPY . .

# Створюємо папку для ефемерид
RUN mkdir -p /app/ephe

# Завантаження ефемерид, якщо папка пуста
RUN test -n "$(ls -A /app/ephe)" || git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph \
    && cp /tmp/swisseph/ephe/* /app/ephe/ \
    && rm -rf /tmp/swisseph

# Порт
EXPOSE 8080

# Запуск Flask
CMD ["python", "app.py"]