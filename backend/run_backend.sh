#!/bin/bash
set -e

CONTAINER_NAME="natal-backend"

# Перевірка, чи існує контейнер
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Контейнер $CONTAINER_NAME вже існує. Зупиняємо та видаляємо..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Знаходимо перший вільний порт 5000-5100
PORT=$(comm -23 <(seq 5000 5100) <(lsof -iTCP -sTCP:LISTEN -P -n | awk '{print $9}' | grep -oE '[0-9]+$') | head -n1)

if [ -z "$PORT" ]; then
    echo "Не вдалося знайти вільний порт у діапазоні 5000-5100!"
    exit 1
fi

echo "Використовуємо локальний порт: $PORT"

# Запуск контейнера
docker run -d \
    -p $PORT:8080 \
    --name $CONTAINER_NAME \
    -v $(pwd)/data/ephe:/data/ephe \
    natal-backend:latest \
    gunicorn -b 0.0.0.0:8080 app:app

URL="http://localhost:$PORT"
echo "Backend доступний за: $URL"

# Відкриваємо URL у браузері
open $URL