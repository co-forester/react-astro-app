# Базовий образ Python 3.9
FROM python:3.9-slim

# Системні залежності для numpy, pyswisseph, flatlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    gfortran \
    pkg-config \
    ca-certificates \
    locales \
    python3-dev \
    libffi-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Директорія для ephe (volume)
RUN mkdir -p /data/ephe

# Копіюємо requirements.txt і кешуємо шар
COPY requirements.txt /app/

# Virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Pip і залежності
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту проєкту
COPY . /app

# Порт Flask
EXPOSE 5000

# Команда запуску
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]