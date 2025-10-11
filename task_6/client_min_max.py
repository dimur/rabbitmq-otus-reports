import asyncio

from rstream import (
    AMQPMessage,  # Импорт AMQP-сообщений, которые будут обрабатываться
    Consumer,     # Импорт потребителя сообщений из rstream
    MessageContext,  # Контекст для обработки сообщений
    ConsumerOffsetSpecification,  # Спецификация смещения для потребителя
    OffsetType,  # Типы смещений для потребителя
)

# Имя потока, с которым будем работать
STREAM_NAME = "test_stream"

# Переменные для отслеживания минимального и максимального значений
min_value = None
max_value = None


async def on_message(msg: AMQPMessage, message_context: MessageContext):
    """
    Обработчик сообщений, который:
    - Преобразует сообщение в число.
    - Обновляет минимальное и максимальное значения.
    - Печатает полученное значение, минимальное и максимальное значения.
    """
    global min_value, max_value

    try:
        # Преобразование тела сообщения в число
        value = float(msg)

        # Обновление минимального и максимального значений
        if min_value is None or value < min_value:
            min_value = value
        if max_value is None or value > max_value:
            max_value = value

        # Печать полученного значения и текущих минимальных и максимальных значений
        print(f"Received value: {value} | Min: {min_value} | Max: {max_value}")

    except ValueError:
        # Если преобразование в число не удалось, печатаем ошибку
        print(f"Invalid value received: {msg}")


async def main():
    """
    Основная асинхронная функция, которая:
    - Создает потребителя для потока.
    - Подключается к потоку и подписывается на его сообщения.
    - Ожидает сообщений и вызывает обработчик.
    """
    
    # Создание потребителя для подключения к RabbitMQ
    consumer = Consumer(
        host="rabbitmq",  # Адрес хоста RabbitMQ
        port=5552,        # Порт для подключения
        username="guest", # Имя пользователя для авторизации
        password="guest", # Пароль для авторизации
    )
    
    # Создание потока, если он еще не существует
    await consumer.create_stream(STREAM_NAME, exists_ok=True)

    # Запуск потребителя для начала получения сообщений
    await consumer.start()

    # Подписка на поток с указанием обработчика сообщений и спецификации смещения
    await consumer.subscribe(
        stream=STREAM_NAME,  # Имя потока
        callback=on_message,  # Функция-обработчик сообщений
        offset_specification=ConsumerOffsetSpecification(OffsetType.FIRST, None),  # Настройка смещения для начала получения сообщений
    )

    # Выводим сообщение о начале работы потребителя
    print("Consumer started. Waiting for messages...")

    # Запуск потребителя для обработки сообщений
    await consumer.run()


if __name__ == "__main__":
    """
    Точка входа в программу.
    Использует asyncio для запуска основной асинхронной функции.
    """
    with asyncio.Runner() as runner:
        runner.run(main())  # Запуск основного цикла обработки событий
