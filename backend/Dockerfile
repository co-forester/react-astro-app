# Базовий образ
FROM python:3.11-slim

# ASCII-анімація + інсталяція залежностей
RUN echo "🚀 Підготовка космічного корабля..." \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        build-essential \
        wget \
        curl \
        libatlas-base-dev \
        gfortran \
        pkg-config \
        ca-certificates \
        locales \
        python3-dev \
    && echo "" \
    && echo "   |" \
    && echo "  / \\" \
    && echo " |   |" \
    && echo "  | |" \
    && echo "  | |" \
    && echo " /   \\" \
    && echo " |NASA|" \
    && echo "  | |" \
    && echo "  | |" \
    && echo " /   \\" \
    && echo "/     \\" \
    && echo "--------" \
    && sleep 1 \
    && echo "🔥 Запалювання двигунів..." && sleep 1 \
    && echo "💨 Відрив від стартового столу..." && sleep 1 \
    && echo "🪐 Політ до зірок!" && sleep 1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо залежності та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту коду
COPY . .

# Запуск
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]