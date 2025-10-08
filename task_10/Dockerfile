FROM python:3.12-slim

RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pika

COPY client.py /app/client.py

WORKDIR /app

CMD ["python", "client.py"]
