# Використовуємо Python 3.10 (сумісний зі swisseph)
FROM python:3.10-slim

# Встановлюємо системні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    wget \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо requirements і встановлюємо залежності Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копіюємо проект
COPY . .

# Скрипт для завантаження ephe при старті
RUN mkdir -p /usr/share/ephe
RUN echo '#!/bin/sh\n\
if [ ! "$(ls -A /usr/share/ephe)" ]; then\n\
  echo "Завантажуємо ефемериди..."\n\
  git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph\n\
  cp /tmp/swisseph/ephe/* /usr/share/ephe/\n\
  rm -rf /tmp/swisseph\n\
fi\n\
exec "$@"' > /start.sh
RUN chmod +x /start.sh

EXPOSE 8080

# Використовуємо скрипт запуску
ENTRYPOINT ["/start.sh"]
CMD ["gunicorn", "--workers=4", "--threads=2", "--timeout=120", "-b", "0.0.0.0:8080", "app:app"]