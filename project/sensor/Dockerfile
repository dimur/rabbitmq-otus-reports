FROM python:3.11-slim

RUN pip install paho-mqtt

COPY publish_mqtt.py /app/publish_mqtt.py
WORKDIR /app

CMD ["python", "publish_mqtt.py"]
