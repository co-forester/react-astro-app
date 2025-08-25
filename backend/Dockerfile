FROM python:3.11

WORKDIR /app

# Системні пакети для numpy, pandas, matplotlib
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ make \
    libgeos-dev libfreetype6-dev libpng-dev libjpeg-dev \
    libffi-dev tar curl wget \
    libgl1 libglib2.0-0 \
    libbz2-dev liblzma-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Встановлюємо прямо у глобальний Python
RUN pip install --upgrade pip wheel setuptools \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x /app/entrypoint.sh

ENV MPLBACKEND="Agg"
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]