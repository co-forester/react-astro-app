#!/bin/bash
set -e

EPHE_DIR="/data/ephe"
EPHE_ARCHIVE="/app/ephe.tar.gz"

# Перевіряємо наявність ефемерид
if [ -z "$(find "$EPHE_DIR" -type f -name '*.se1' | head -n 1)" ]; then
    echo "Ефемериди не знайдені у volume."
    if [ -f "$EPHE_ARCHIVE" ]; then
        echo "Розпаковуємо $EPHE_ARCHIVE у $EPHE_DIR ..."
        mkdir -p "$EPHE_DIR"
        tar -xzf "$EPHE_ARCHIVE" -C "$EPHE_DIR"
        echo "Розпаковка завершена."
    else
        echo "Файл ефемерид $EPHE_ARCHIVE не знайдено! Продовжуємо без ефемерид."
    fi
else
    echo "Ефемериди знайдені у volume. Пропускаємо розпаковку."
fi

# Запускаємо основну команду (Gunicorn)
exec "$@"