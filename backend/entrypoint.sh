#!/bin/bash
set -e

# Перевіряємо, чи є хоча б один .se1 файл або інші ефемериди в /data/ephe
if [ -z "$(find /data/ephe -type f -name '*.se1' | head -n 1)" ]; then
    echo "Ефемериди не знайдені у volume, розпаковуємо..."
    mkdir -p /data/ephe
    tar -xzf /app/ephe.tar.gz -C /data/ephe
else
    echo "Ефемериди знайдені у volume. Пропускаємо розпаковку."
fi

# Запускаємо основну команду (Gunicorn)
exec "$@"