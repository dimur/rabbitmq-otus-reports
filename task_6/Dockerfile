FROM python:3.12-slim

RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        pika \
        rstream

COPY *.py /app/

WORKDIR /app

CMD ["sleep", "infinity"]
