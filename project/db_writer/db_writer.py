from datetime import datetime
import json
import logging
import os
import paho.mqtt.client as mqtt
import psycopg2
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

# -----------------------------------------
# Параметры подключения к базе TimescaleDB
# -----------------------------------------
DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "metrics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

# Глобальная переменная подключения
conn = None


def connect_db():
    """
    Устанавливает соединение с TimescaleDB.
    Включает autocommit для упрощённой вставки данных.
    """
    global conn
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    logging.info("Connected to TimescaleDB")


def create_table():
    """
    Создаёт таблицу temperature (если ещё не существует)
    и преобразует её в hypertable — специальный формат TimescaleDB
    для хранения временных рядов.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS temperature (
                time TIMESTAMPTZ NOT NULL,
                sensor TEXT NOT NULL,
                value DOUBLE PRECISION NOT NULL
            );
        """)

        # Преобразование в hypertable
        cur.execute("""
            SELECT create_hypertable('temperature', 'time', if_not_exists => TRUE);
        """)

    logging.info("Table temperature is ready (hypertable created)")


def on_connect(client, userdata, flags, rc):
    """
    Запускается при подключении к MQTT-брокеру.
    Если rc == 0 — подключение успешное.
    Выполняется подписка на указанный топик.
    """
    if rc == 0:
        logging.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")

        client.subscribe(MQTT_TOPIC, qos=1)
        logging.info(f"Subscribed to topic '{MQTT_TOPIC}'")
    else:
        logging.error(f"Failed to connect to MQTT broker with code {rc}")


def on_message(client, userdata, msg):
    """
    Обрабатывает каждое входящее сообщение MQTT:
    - парсит JSON
    - извлекает время и значение датчика
    - записывает данные в базу TimescaleDB
    """
    try:
        # Декодируем JSON-пакет
        payload = json.loads(msg.payload.decode())

        value = payload.get('value')
        timestamp_ms = payload.get('timestamp')

        # Проверка корректности данных
        if value is None or timestamp_ms is None:
            logging.warning(f"Skipping message with missing fields: {msg.payload}")
            return

        # Конвертация timestamp из миллисекунд в datetime
        timestamp = datetime.utcfromtimestamp(int(timestamp_ms) / 1000.0)

        # Имя сенсора берётся из последней части MQTT-топика
        sensor = msg.topic.split('/')[-1]

        # Запись в базу
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO temperature (time, sensor, value) VALUES (%s, %s, %s);",
                (timestamp, sensor, float(value))
            )

        logging.info(f"Saved data: sensor={sensor}, value={value}, time={timestamp}")

    except Exception as e:
        logging.error(f"Failed to process message: {e}")


# -----------------------------------------
# Основная функция
# -----------------------------------------
def main():
    """
    Запускает приложение:
    - подключение к БД
    - создание таблицы
    - запуск MQTT-клиента
    """
    connect_db()
    create_table()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Подключаемся к брокеру и запускаем бесконечный цикл обработки сообщений
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


# -----------------------------------------
# Точка входа в приложение
# -----------------------------------------
if __name__ == "__main__":
    # Задержка перед первым подключением (даёт брокеру время на запуск)
    time.sleep(60)
    main()
