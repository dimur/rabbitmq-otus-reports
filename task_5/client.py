import pika, os, uuid, time

# Параметры подключения к RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
# Имена для обменников типа header и fanout
EXCHANGE_MAIN = "main"
EXCHANGE_BROADCAST = "broadcast"

def main():
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

    # Создание обменника типа headers с именем main
    channel.exchange_declare(
        exchange=EXCHANGE_MAIN,
        exchange_type='headers',
        durable=True
    )

    # Создание обменника типа fanout с именем broadcast
    channel.exchange_declare(
        exchange=EXCHANGE_BROADCAST,
        exchange_type='fanout',
        durable=True
    )

    # Создание привязки между обменниками main и broadcast по header type=request
    channel.exchange_bind(
        destination=EXCHANGE_BROADCAST,
        source=EXCHANGE_MAIN,
        arguments={
            "x-match": "all",
            "type": "request"
        }
    )

    # Генерация уникального id для идентификации экземпляра приложения
    unique_id = str(uuid.uuid4())
    print(f"Client with id {unique_id} is started")

    # Создание отдельной очереди для экземпляра приложения с именем равным unique_id
    channel.queue_declare(queue=unique_id, durable=True)

    # Создание привязки обменника main к очереди по header type=reply и to=unique_id
    channel.queue_bind(
        exchange=EXCHANGE_MAIN,
        queue=unique_id,
        arguments={
            'x-match': 'all',
            'type': 'reply',
            'to': unique_id
        }
    )

    # Создание привязки обменника broadcast к той же очереди
    channel.queue_bind(exchange=EXCHANGE_BROADCAST, queue=unique_id)

    print("Exchanges, queues and bindings created successfully")

    time.sleep(10)  # Пауза на 10 секунд, чтобы все экземпляры приложения
                    # успели запуститься и были готовы к отправке и получению сообщений

    # Отправка broadcast сообщения
    message_body = "Broadcast request message"
    headers = {
        'type': 'request',
        'from': unique_id
    }
    channel.basic_publish(
        exchange='main',
        routing_key='',
        properties=pika.BasicProperties(headers=headers),
        body=message_body.encode()
    )

    print(f" [>>] Sent broadcast request with headers: {headers}")

    # Обработка получения сообщений из очереди unique_id
    def callback(ch, method, properties, body):
        headers = properties.headers or {}

        msg_type = headers.get('type')
        msg_from = headers.get('from')

        # Проверка типа сообщения
        if msg_type == 'request' and msg_from:
            # Ответ отправителю на сообщение типа request
            print(f" [<<] Received broadcast request: {body.decode()} with headers: {headers}")
            reply_headers = {
                'type': 'reply',
                'from': unique_id,
                'to': msg_from
            }
            reply_body = f"Reply to message from {msg_from}"

            ch.basic_publish(
                exchange='main',
                routing_key='',
                properties=pika.BasicProperties(headers=reply_headers),
                body=reply_body.encode()
            )
            print(f" [>] Sent reply with headers: {reply_headers}")

        elif msg_type == 'reply':
            # Получение сообщения типа reply (только вывод)
            print(f" [<] Received reply: {body.decode()} with headers: {headers}")

        else:
            # Получение сообщения типа прочих типов (только вывод)
            print(f" [!] Received message with unknown or missing type: {body.decode()} with headers: {headers}")

        # Подтверждение получение сообщения
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=unique_id,
        on_message_callback=callback,
        auto_ack=False
    )

    print(f" [*] Waiting for messages in queue {unique_id}.")
    channel.start_consuming()

if __name__ == "__main__":
    main()
