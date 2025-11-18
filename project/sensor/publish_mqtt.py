from paho.mqtt.client import CallbackAPIVersion
import json
import logging
import os
import paho.mqtt.client as mqtt
import random
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

# Топик MQTT, куда будет публиковаться значение температуры
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "temperature/data_center_a1")

# Сохранять последнее сообщение на брокере
MQTT_RETAIN = os.getenv("MQTT_RETAIN", "true").lower() == "true"

# Интервал публикации новых данных (в секундах)
PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "60"))


def on_connect(client, userdata, flags, reasonCode, properties=None):
    """
    Вызывается после подключения к MQTT-брокеру.
    reasonCode == 0 → подключение прошло успешно.
    """
    if reasonCode == 0:
        logging.info("Connected to MQTT broker successfully")
    else:
        logging.error(f"Failed to connect, return code {reasonCode}")


def on_disconnect(client, userdata, reasonCode, properties=None):
    """
    Вызывается при отключении клиента.
    reasonCode содержит код причины.
    """
    logging.info(f"Disconnected from MQTT broker with code {reasonCode}")


def publish_periodically():
    """
    Циклически публикует данные в MQTT:
    - генерирует случайную температуру
    - добавляет timestamp (мс)
    - отправляет JSON в указанный топик
    """
    while True:
        # Генерация данных: температура от 10 до 40
        value = random.randint(10, 40)

        # Метка времени (в миллисекундах)
        timestamp_ms = int(time.time() * 1000)

        # Формирование JSON-сообщения
        mqtt_message = json.dumps({
            "value": value,
            "timestamp": timestamp_ms
        })

        # Публикация в MQTT
        try:
            result = client.publish(
                MQTT_TOPIC,       # Топик
                mqtt_message,     # Сообщение
                qos=1,            # Доставка "как минимум один раз"
                retain=MQTT_RETAIN
            )

            # Проверяем статус отправки
            status = result.rc
            if status == mqtt.MQTT_ERR_SUCCESS:
                logging.info(
                    f"Published message '{mqtt_message}' "
                    f"to topic '{MQTT_TOPIC}' on {MQTT_HOST}:{MQTT_PORT} "
                    f"with retain={MQTT_RETAIN}"
                )
            else:
                logging.error(
                    f"Failed to publish message '{mqtt_message}', "
                    f"error code: {status}"
                )
        except Exception as e:
            logging.error(f"Exception during publish: {e}")

        # Пауза между публикациями
        time.sleep(PUBLISH_INTERVAL)


# -----------------------------------------
# Создание MQTT-клиента
# -----------------------------------------
# Используем API версии 2 (рекомендуется paho-mqtt)
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

# Привязка callback-функций
client.on_connect = on_connect
client.on_disconnect = on_disconnect


# -----------------------------------------
# Точка входа
# -----------------------------------------
if __name__ == "__main__":
    # Задержка перед первым подключением (даёт брокеру время на запуск)
    time.sleep(PUBLISH_INTERVAL)

    try:
        # Подключение к брокеру MQTT
        client.connect(MQTT_HOST, MQTT_PORT, 60)

        # Запуск фонового цикла обработки MQTT-событий
        client.loop_start()

        # Бесконечная отправка данных
        publish_periodically()
    except Exception as e:
        logging.error(f"Error connecting to MQTT broker: {e}")
        client.loop_stop()
