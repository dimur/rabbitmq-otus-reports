#!/usr/bin/env bash
set -e

NODE_NAME=$1
CLUSTER_WITH=${2:-}

rabbitmq-server -detached

echo "Waiting for rabbitmq node to start..."
until rabbitmqctl status &> /dev/null; do
  sleep 3
done

if [ -n "$CLUSTER_WITH" ]; then
  echo "Stopping app on $NODE_NAME"
  rabbitmqctl stop_app

  echo "Resetting node $NODE_NAME"
  rabbitmqctl reset

  echo "Joining cluster with rabbit@$CLUSTER_WITH"
  rabbitmqctl join_cluster rabbit@$CLUSTER_WITH
  
  echo "Starting app on $NODE_NAME"
  rabbitmqctl start_app
fi

echo "Cluster status on $NODE_NAME:"
rabbitmqctl cluster_status

echo "Switching to foreground"
rabbitmqctl stop
rabbitmq-server
