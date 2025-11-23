Оценить пропускную способность RabbitMQ на компьютере (самостоятельно оценить пропускную способность RMQ с помощью инструмента PerfTest. 
Изучить влияние размера сообщения и функции prefech на производительность). 
Результаты замеров свести в таблицу.  

### Описание/Пошаговая инструкция выполнения домашнего задания  
1. Установить утилиту в perf-test.
2. Тестирование классических очередей.
3. Тестирование кворумных очередей.

### Запуск решения  
Нужно развернуть локальный кластер RabbitMQ (1 узел для классики и стрима, 3 узла для кворума), запустить perf-test в отдельных контейнерах, прогнать несколько серий тестов с разным размером сообщений и prefetch  

```
# Базовые тесты
docker-compose -f docker-compose.yaml up -d
docker exec -it perf-test bash
> # Prefetch = 1, 1000; Size = 100, 1000, 10000
> java -jar perf-test.jar \
>   --uri amqp://rabbit1 \
>   --producers 1 \
>   --consumers 1 \
>   --size 100 \
>   --qos 1 \
>   --time 60 \
>   --queue "classic-q-prefetch-1" \
>   --use-millis \
>   --auto-delete false

# Тест стримов
docker exec -it rabbit1 rabbitmq-plugins enable rabbitmq_stream
docker exec -it perf-test-stream bash
> java -jar stream-perf-test.jar \
>   --uris rabbitmq-stream://guest:guest@rabbit1:5552 \
>   --streams mystream \
>   --producers 1 \
>   --consumers 1 \
>   --size 100 \
>   --time 60

docker-compose -f docker-compose.yaml down



# Тест для Quorum queue
docker-compose -f docker-compose-cluster.yaml up -d --build
docker exec -it perf-test bash
> java -jar perf-test.jar \
>   --uri amqp://guest:guest@rabbitmq1:5672 \
>   --quorum-queue \
>   --queue "quorum-queue" \
>   --producers 1 \
>   --consumers 0 \
>   --size 1000 \
>   --time 60
>
> java -jar perf-test.jar \
>   --uri amqp://guest:guest@rabbitmq2:5672 \
>   --quorum-queue \
>   --queue "quorum-queue" \
>   --producers 0 \
>   --consumers 1 \
>   --size 1000 \
>   --time 60

# Тест для Classic mirrored queue
docker exec -it rabbitmq1 bash
> rabbitmqctl set_policy ha-all "^classic-mirror-.*" '{"ha-mode":"all"}' --apply-to queues
> rabbitmqctl list_policies

docker exec -it perf-test bash
> java -jar perf-test.jar \
>   --uri amqp://guest:guest@rabbitmq1:5672 \
>   --queue "classic-mirror-q" \
>   --producers 1 \
>   --consumers 0 \
>   --size 1000 \
>   --time 60
>
> java -jar perf-test.jar \
>   --uri amqp://guest:guest@rabbitmq2:5672 \
>   --queue "classic-mirror-q" \
>   --producers 0 \
>   --consumers 1 \
>   --size 1000 \
>   --time 60

docker-compose -f docker-compose-cluster.yaml up down
```

Management интерфейс доступен с кредами `guest:guest` по адресу http://localhost:15672  

### Результаты тестирования пропускной способности RabbitMQ

| Сценарий                                                   | Sent msg/sec | Recv msg/sec | Latency p95 |
|------------------------------------------------------------|--------------|--------------|-----------------------------|
| Quorum Queue, запись на мастер, чтение с реплики           | 3,329        | 3,333     | -        |
| Classic mirrored queue, запись на мастер, чтение с реплики | 7,581        | 6,868     | -        |
| Classic queue, size 100, prefetch count 1                  | 20,104       | 441       | 58083 ms |
| Classic queue, size 1000, prefetch count 1                 | 15,466       | 359       | 57600 ms |
| Classic queue, size 10000, prefetch count 1                | 7,762        | 185       | 57263 ms |
| Classic queue, size 100, prefetch count 1000               | 29,836       | 29,818    | 96 ms    |
| Classic queue, size 1000, prefetch count 1000              | 20,174       | 20,173    | 110 ms   |
| Classic queue, size 10000, prefetch count 1000             | 11,651       | 11,649    | 87 ms    |
| Stream, size 100                                           | 485,504      | 485,337   | 44 ms    |

### Выводы
1. Скорость записи и чтения для Quorum Queue значительно ниже, чем у классических очередей. Возможно это связано с внутренней репликацией и консенсусом (RAFT), обеспечивающим высокую надёжность, но тормозящим производительность, по крайней мере в текущих условиях проведения тестирования.
2. Ограничение prefetch = 1 сильно замедляет потребителей, так как они обрабатывают только одно сообщение за раз, что создаёт узкое место. Высокий prefetch значительно улучшает throughput и уменьшает задержки, позволяя потребителям получать много сообщений одномоментно.
3. Потоковые очереди (streams) демонстрируют очень высокую производительность и низкие задержки, что делает их оптимальным выбором для высоконагруженных систем, когда важна скорость и масштабируемость.
