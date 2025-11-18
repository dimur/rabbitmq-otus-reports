FROM rabbitmq:management

RUN rabbitmq-plugins enable --offline rabbitmq_mqtt && \
    rabbitmq-plugins enable --offline rabbitmq_web_mqtt

COPY cluster-entrypoint.sh /usr/local/bin/cluster-entrypoint.sh

RUN chmod +x /usr/local/bin/cluster-entrypoint.sh
