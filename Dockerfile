FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    build-base \
    python3-dev \
    cargo \
    && pip install --upgrade pip

ADD requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

CMD ["uvicorn", \
     "service.main:app", \
     "--host", "0.0.0.0", \
     "--port", "80", \
     "--workers", "2", \
     "--log-config", "log_config.yaml"]
