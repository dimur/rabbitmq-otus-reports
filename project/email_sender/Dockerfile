FROM python:3.11-slim

WORKDIR /app

RUN pip install paho-mqtt

COPY mqtt_email_alert.py /app/mqtt_email_alert.py

CMD ["python", "/app/mqtt_email_alert.py"]
