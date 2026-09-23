"""At-least-once RabbitMQ: publisher confirms + inbox + manual ack."""

import json
import logging
import os
import time

import pika

log = logging.getLogger(__name__)
SERVICES = ("rental", "inventory", "billing")


def topology(channel):
    channel.exchange_declare(exchange="rental.events", exchange_type="direct", durable=True)
    channel.exchange_declare(exchange="rental.dead", exchange_type="direct", durable=True)
    for name in SERVICES:
        channel.queue_declare(queue=f"{name}.dead", durable=True)
        channel.queue_bind(queue=f"{name}.dead", exchange="rental.dead", routing_key=name)
        channel.queue_declare(
            queue=f"{name}.events",
            durable=True,
            arguments={"x-dead-letter-exchange": "rental.dead", "x-dead-letter-routing-key": name},
        )
        channel.queue_bind(queue=f"{name}.events", exchange="rental.events", routing_key=name)
    channel.basic_qos(prefetch_count=1)
    channel.confirm_delivery()


def publish_pending(factory, channel):
    # Сбой между confirm и commit допускает повторную публикацию, но не потерю события.
    with factory() as uow:
        for event in uow.pending_events():
            channel.basic_publish(
                exchange="rental.events",
                routing_key=event["target"],
                body=json.dumps(event).encode(),
                mandatory=True,
                properties=pika.BasicProperties(
                    delivery_mode=2, content_type="application/json", message_id=event["id"]
                ),
            )
            uow.mark_published(event["id"])


def consume_event(factory, handler, event):
    if not isinstance(event, dict) or not isinstance(event.get("payload"), dict):
        raise ValueError("Invalid event envelope")
    if not all(isinstance(event.get(k), str) for k in ("id", "type", "target")):
        raise ValueError("Invalid event headers")
    with factory() as uow:
        if uow.seen(event["id"]):
            return
        handler(uow, event)
        # Изменения агрегатов, исходящие события и inbox фиксируются одной транзакцией.
        uow.remember(event["id"])


def tick(name, factory, handler, channel):
    publish_pending(factory, channel)
    method, properties, body = channel.basic_get(queue=f"{name}.events", auto_ack=False)
    if method is None:
        return False
    try:
        event = json.loads(body)
        if event.get("target") != name:
            raise ValueError("Wrong target")
        consume_event(factory, handler, event)
    except (ValueError, KeyError, TypeError):
        log.exception("Invalid event routed to dead-letter queue")
        channel.basic_nack(method.delivery_tag, requeue=False)
    except Exception:
        log.exception("Transient processing failure; event will be retried")
        channel.basic_nack(method.delivery_tag, requeue=True)
        time.sleep(1)
    else:
        channel.basic_ack(method.delivery_tag)
    return True


def run_worker(name, factory, handler):
    logging.basicConfig(level=logging.INFO)
    while True:
        connection = None
        try:
            parameters = pika.URLParameters(os.environ["RABBITMQ_URL"])
            parameters.heartbeat = 30
            parameters.blocked_connection_timeout = 10
            parameters.socket_timeout = 5
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            topology(channel)
            while connection.is_open:
                if not tick(name, factory, handler, channel):
                    connection.sleep(0.2)
        except KeyboardInterrupt:
            return
        except Exception:
            log.exception("Worker disconnected; reconnecting")
            time.sleep(2)
        finally:
            if connection is not None and connection.is_open:
                connection.close()
