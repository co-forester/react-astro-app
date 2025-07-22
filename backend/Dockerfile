FROM python:3.10.18 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py

WORKDIR /app

RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.10.18-slim

ENV FLASK_APP=app.py

WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

CMD ["/app/.venv/bin/flask", "run", "--host=0.0.0.0", "--port=8080"]