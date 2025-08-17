#!/bin/bash
set -e

if [ ! -f /data/ephe/sepl_18.se1 ]; then
    echo "Ефемериди не знайдені у volume, розпаковуємо..."
    mkdir -p /data/ephe
    tar -xzf /app/ephe.tar.gz -C /data/ephe
else
    echo "Ефемериди знайдені у volume. Пропускаємо розпаковку."
fi

exec "$@"