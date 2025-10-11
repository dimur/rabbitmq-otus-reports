import asyncio
import heapq  # Для работы с кучами, используемыми для вычисления медианы

from rstream import (
    AMQPMessage,  # Импорт AMQP-сообщений для обработки входящих сообщений
    Consumer,     # Импорт Consumer для потребления сообщений
    MessageContext,  # Контекст сообщения для обработки
    ConsumerOffsetSpecification,  # Спецификация смещения для потребителя
    OffsetType,  # Типы смещений для потребителя
)

# Имя потока, с которым будем работать
STREAM_NAME = "test_stream"


class MedianFinder:
    """
    Класс для нахождения медианы.
    Использует две кучи: small для больших элементов и large для меньших.
    """
    def __init__(self):
        # small - малая куча для хранения больших половин чисел (с инверсией знака)
        self.small = []  
        # large - большая куча для хранения меньших половин чисел
        self.large = []

    def add_num(self, num):
        """
        Добавление числа в структуры данных для поддержания медианы.
        Число добавляется в кучу small (с инверсией), чтобы на вершине small всегда было максимальное число.
        Если количество элементов в small больше, чем в large, переносим элемент из small в large.
        Если в large больше элементов, переносим из него элемент обратно в small.
        """
        # Добавляем число в small (с инверсией знака)
        heapq.heappush(self.small, -num)

        # Переносим максимальный элемент из small в large
        heapq.heappush(self.large, -heapq.heappop(self.small))

        # Если в large больше элементов, переносим из large обратно в small
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self):
        """
        Находим медиану:
        - Если в small больше элементов, медианой является максимальное число из small.
        - Если куча small и large равны по размеру, медианой является среднее арифметическое их корней.
        """
        if len(self.small) > len(self.large):
            # Медиана для нечетного числа элементов
            return float(-self.small[0])
        else:
            # Медиана для четного числа элементов
            return (-self.small[0] + self.large[0]) / 2.0


# Создаем объект для нахождения медианы
median_finder = MedianFinder()


async def on_message(msg: AMQPMessage, message_context: MessageContext):
    """
    Обработчик сообщений, который:
    - Преобразует сообщение в число.
    - Добавляет число в медианную структуру.
    - Печатает медиану после каждого нового сообщения.
    """
    try:
        # Преобразуем тело сообщения в число
        value = float(msg)
        
        # Добавляем число в медианную структуру
        median_finder.add_num(value)
        
        # Находим медиану
        median = median_finder.find_median()
        
        # Печатаем полученное значение и текущую медиану
        print(f"Received value: {value} | Median: {median:.4f}")
    
    except ValueError:
        # Если сообщение не удалось преобразовать в число, выводим ошибку
        print(f"Invalid value received: {msg}")


async def main():
    """
    Основная асинхронная функция, которая:
    - Создает потребителя для подключения к RabbitMQ.
    - Подключается к потоку и подписывается на его сообщения.
    - Обрабатывает сообщения и находит медиану.
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

    # Запуск потребителя для получения сообщений
    await consumer.start()

    # Подписка на поток с указанием обработчика сообщений и спецификации смещения
    await consumer.subscribe(
        stream=STREAM_NAME,  # Имя потока
        callback=on_message,  # Функция-обработчик сообщений
        offset_specification=ConsumerOffsetSpecification(OffsetType.FIRST, None),  # Настройка смещения
    )

    # Сообщение о старте потребителя
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
