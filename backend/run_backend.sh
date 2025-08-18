#!/bin/bash
set -e

CONTAINER_NAME="natal-backend"
IMAGE_NAME="natal-backend:latest"
HOST_PORT=5000
CONTAINER_PORT=8080

# Видаляємо старий контейнер, якщо існує
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Зупиняємо та видаляємо старий контейнер..."
    docker rm -f $CONTAINER_NAME
fi

# Запускаємо новий контейнер
echo "Запускаємо $CONTAINER_NAME на порту $HOST_PORT..."
docker run -d -p $HOST_PORT:$CONTAINER_PORT --name $CONTAINER_NAME $IMAGE_NAME

# Перевіряємо логи
docker logs -f $CONTAINER_NAME