FROM python:3.11-slim

WORKDIR /app

RUN pip install paho-mqtt psycopg2-binary

COPY db_writer.py /app/db_writer.py

CMD ["python", "/app/db_writer.py"]
