#!/bin/bash

MAX_RETRIES=5
SLEEP_SEC=5
COUNT=0

while [ $COUNT -lt $MAX_RETRIES ]; do
    echo "Спроба $((COUNT+1)) запуску контейнера..."
    
    # Видаляємо старий контейнер, якщо існує
    docker rm -f natal-backend 2>/dev/null || true
    
    # Запускаємо контейнер
    docker run -d -p 8080:8080 --name natal-backend natal-backend:latest
    
    # Чекаємо кілька секунд, щоб контейнер стартував
    sleep $SLEEP_SEC
    
    # Перевіряємо доступність сервера
    if curl -s http://localhost:8080 >/dev/null; then
        echo "Сервер запущено успішно!"
        docker ps --filter "name=natal-backend"
        exit 0
    else
        echo "Не вдалося підключитися, спробуємо знову через $SLEEP_SEC секунд..."
        COUNT=$((COUNT+1))
    fi
done

echo "Не вдалося запустити сервер після $MAX_RETRIES спроб."
exit 1