import asyncio
import random
from rstream import Producer

# Имя потока, с которым будем работать
STREAM_NAME = "test_stream"

async def main():
    """
    Основная асинхронная функция, которая:
    - Подключается к RabbitMQ с использованием rstream Producer.
    - Создает или подключается к потоку STREAM_NAME.
    - Отправляет случайные числа в поток каждую минуту.
    """
    
    # Создание асинхронного контекстного менеджера для подключения к RabbitMQ
    async with Producer(
        host="rabbitmq",  # Адрес хоста RabbitMQ
        port=5552,        # Порт для подключения
        username="guest", # Имя пользователя для авторизации
        password="guest"  # Пароль для авторизации
    ) as producer:
        
        # Создание потока, если он еще не существует
        await producer.create_stream(STREAM_NAME, exists_ok=True)
        print(f"Stream '{STREAM_NAME}' created or already exists")
        
        # Вечный цикл, отправляющий случайные числа в поток каждую минуту
        while True:
            # Генерация случайного числа от 0 до 100
            number = random.randint(0, 100)
            
            # Отправка числа в поток, кодируем его в байты перед отправкой
            await producer.send(STREAM_NAME, str(number).encode())
            print(f"Sent: {number}")
            
            # Ожидание 60 секунд перед отправкой следующего числа
            await asyncio.sleep(60)


if __name__ == "__main__":
    """
    Точка входа в программу.
    Использует asyncio для запуска основной асинхронной функции.
    """
    with asyncio.Runner() as runner:
        runner.run(main())  # Запуск основного цикла обработки событий
