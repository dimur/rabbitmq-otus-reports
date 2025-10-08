import pika, os, time

# Параметры подключения к RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "nginx")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
# Имена для обменников типа header и fanout
QUEUE_NAMES = ['ha.queue1', 'ha.queue2', 'ha.queue3']

def main():
    time.sleep(30) # пауза, чтобы кластер успел "собраться" и все ноды были связаны
    # Подключение к RabbitMQ
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    )
    channel = connection.channel()

    # Создание высокодоступных очередей
    for name in QUEUE_NAMES:
        channel.queue_declare(queue=name, durable=True, arguments={"x-queue-type": "quorum"})
        channel.basic_publish(exchange='', routing_key=name, body=f'Message for {name}')

    connection.close()
if __name__ == "__main__":
    main()
