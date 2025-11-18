from email.message import EmailMessage
import json
import logging
import os
import paho.mqtt.client as mqtt
import smtplib
import time

# -----------------------------------------
# Настройка логирования
# -----------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# -----------------------------------------
# Параметры MQTT
# -----------------------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "rabbitmq1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "temperature/#")

# Порог температуры: при превышении отправляется email-алерт
TEMPERATURE_THRESHOLD = float(os.getenv("TEMPERATURE_THRESHOLD", "25.0"))

# -----------------------------------------
# Параметры SMTP (Mailpit, Postfix, etc.)
# -----------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "alert@example.com")
EMAIL_TO = os.getenv("EMAIL_TO", "user@example.com")


def send_email(subject: str, body: str):
    """
    Отправляет email через указанный SMTP-сервер.
    Используется для алертов о превышении температуры.
    """
    msg = EmailMessage()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        # Подключение к SMTP-серверу и отправка сообщения
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.send_message(msg)

        logging.info(f"Sent alert email to {EMAIL_TO}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def on_connect(client, userdata, flags, rc):
    """
    Вызывается при подключении к брокеру.
    rc == 0 → подключение успешно.
    После успешного подключения подписываемся на топик.
    """
    if rc == 0:
        logging.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")

        # Подписка на выбранный топик (можно использовать шаблоны: temperature/#)
        client.subscribe(MQTT_TOPIC, qos=1)
        logging.info(f"Subscribed to topic '{MQTT_TOPIC}'")
    else:
        logging.error(f"Failed to connect to MQTT broker with code {rc}")


def on_message(client, userdata, msg):
    """
    Получает сообщение из MQTT, парсит JSON или числовое значение,
    сравнивает температуру с порогом и отправляет email при превышении.
    """
    try:
        # Пытаемся интерпретировать payload как JSON
        payload = json.loads(msg.payload.decode())

        # Получение температуры. Если payload — число, используем его напрямую.
        temp_value = payload.get("value") or float(payload)

        logging.info(f"Received temperature {temp_value} on topic {msg.topic}")

        # Проверка: превышена ли температура
        if float(temp_value) > TEMPERATURE_THRESHOLD:
            subject = f"Temperature Alert: {temp_value}°C on {msg.topic}"
            body = (
                f"Temperature exceeded threshold {TEMPERATURE_THRESHOLD}°C.\n"
                f"Value: {temp_value}\n"
                f"Topic: {msg.topic}"
            )
            send_email(subject, body)

    except Exception as e:
        logging.error(f"Error processing message: {e}")


# -----------------------------------------
# Основная функция — запуск MQTT-клиента
# -----------------------------------------
def main():
    # Создаём MQTT-клиента
    client = mqtt.Client()

    # Привязываем callback-функции
    client.on_connect = on_connect
    client.on_message = on_message

    # Подключаемся и запускаем главный цикл
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


# -----------------------------------------
# Точка входа
# -----------------------------------------
if __name__ == "__main__":
    # Задержка перед первым подключением (даёт брокеру время на запуск)
    time.sleep(60)
    main()
