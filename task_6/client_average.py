import asyncio

from rstream import (
    AMQPMessage,  # Импорт AMQP-сообщений для обработки входящих сообщений
    Consumer,     # Импорт Consumer для потребления сообщений
    MessageContext,  # Контекст сообщения для обработки
    ConsumerOffsetSpecification,  # Спецификация смещения для потребителя
    OffsetType,  # Типы смещений для потребителя
)

# Имя потока, с которым будем работать
STREAM_NAME = "test_stream"

# Переменные для хранения суммы значений и количества сообщений
total = 0.0
count = 0


async def on_message(msg: AMQPMessage, message_context: MessageContext):
    """
    Обработчик сообщений, который:
    - Преобразует сообщение в число.
    - Рассчитывает среднее значение всех полученных чисел.
    - Печатает полученное значение и текущее среднее.
    """
    global total, count
    try:
        # Преобразование тела сообщения в число
        value = float(msg)

        # Обновление суммы всех значений и количества сообщений
        total += value
        count += 1

        # Рассчитываем среднее значение и выводим его
        average = total / count
        print(f"Received value: {value} | Average: {average:.4f}")

    except ValueError:
        # Если сообщение не удалось преобразовать в число, печатаем ошибку
        print(f"Invalid value received: {msg}")


async def main():
    """
    Основная асинхронная функция, которая:
    - Создает потребителя для потока.
    - Подключается к потоку и подписывается на его сообщения.
    - Обрабатывает сообщения, вычисляя среднее значение.
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
