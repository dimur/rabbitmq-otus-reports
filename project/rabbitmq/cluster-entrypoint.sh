#!/usr/bin/env bash
# Скрипт для автоматического включения узла RabbitMQ в кластер.
# Работает внутри контейнера, запускаемого вторичными и третьими узлами.
# Формирует готовый кластер RabbitMQ при старте.

set -euo pipefail

# Имя текущего RabbitMQ-узла (например rabbitmq2)
NODE_NAME="$1"

# Имя узла, с которым надо объединиться в кластер (например rabbitmq1)
# Может быть пустым — в этом случае кластеризация пропускается.
CLUSTER_WITH="${2:-}"

echo "$(date -u +"%Y-%m-%d %T UTC") Starting RabbitMQ node ${NODE_NAME}..."

# -----------------------------------------
# Запуск RabbitMQ в фоне (detached mode)
# -----------------------------------------
rabbitmq-server -detached

echo "Waiting for rabbitmqctl..."
# Ожидание, пока управление через rabbitmqctl станет доступно
until rabbitmqctl status > /dev/null 2>&1; do
  sleep 2
done

# -----------------------------------------
# Если передан параметр CLUSTER_WITH — объединяемся в кластер
# -----------------------------------------
if [ -n "${CLUSTER_WITH}" ]; then
  echo "Clustering enabled: will join rabbit@${CLUSTER_WITH}"

  # Проверяем доступность ведущего узла
  echo "Waiting for rabbit@${CLUSTER_WITH} to respond..."
  until rabbitmqctl -n rabbit@"${CLUSTER_WITH}" ping > /dev/null 2>&1; do
    sleep 2
  done

  # Останавливаем локальное приложение RabbitMQ перед присоединением
  echo "Stopping app on this node..."
  rabbitmqctl stop_app

  # Полный сброс локального состояния (необходимо перед join_cluster)
  echo "Resetting node (clearing local cluster state)..."
  rabbitmqctl reset

  # Присоединяемся к кластеру
  echo "Joining cluster rabbit@${CLUSTER_WITH} ..."
  rabbitmqctl join_cluster rabbit@"${CLUSTER_WITH}"

  # Запускаем приложение обратно
  echo "Starting app..."
  rabbitmqctl start_app
fi

# Выводим статус кластера (не критично, поэтому || true)
rabbitmqctl cluster_status || true

# -----------------------------------------
# Сохраняем контейнер "живым":
# tail читает вывод PID=1 (docker stdout)
# -----------------------------------------
exec tail -F /proc/1/fd/1
