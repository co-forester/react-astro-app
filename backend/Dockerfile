FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libgeos-dev \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Якщо маєш файли ефемерид, скопіюй їх у потрібну папку, наприклад /usr/share/ephe
# COPY ephe /usr/share/ephe

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]