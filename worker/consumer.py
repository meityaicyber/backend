import asyncio
import logging
import json
import os
from confluent_kafka import Consumer, KafkaException
from processor import process_document

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = "ingestion_v1"
GROUP_ID = "cyber-audit-workers"

_consumer = None
_running = False

def create_consumer():
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False # WE MANUALLY COMMIT OFFSETS
    }
    return Consumer(conf)

async def consume_loop():
    global _consumer, _running
    _consumer = create_consumer()
    _consumer.subscribe([TOPIC])
    _running = True

    logging.info(f"Worker started. Consuming from {TOPIC}...")

    # We use an async loop to poll Kafka, handing off tasks to the processor
    # to achieve the required 25 concurrent pipelines per worker.
    # We use a semaphore to limit concurrent processing.
    sem = asyncio.Semaphore(25)
    pending_tasks = set()

    async def _handle_msg(msg):
        try:
            payload = json.loads(msg.value().decode('utf-8'))
            success = await process_document(payload)
            if success:
                # Manual Offset Commit ONLY AFTER successful DB transaction
                _consumer.commit(message=msg, asynchronous=True)
        except Exception as e:
            logging.error(f"Message handling error: {e}")
        finally:
            sem.release()

    while _running:
        # Polling is blocking in confluent-kafka, so we yield briefly to event loop if needed,
        # but a small timeout is fine.
        msg = _consumer.poll(timeout=0.1)
        
        if msg is None:
            await asyncio.sleep(0.01)
            continue
        if msg.error():
            logging.error(f"Kafka error: {msg.error()}")
            continue

        # Wait for a slot in the semaphore (max 25 concurrency per worker)
        await sem.acquire()
        
        # Fire and forget task
        task = asyncio.create_task(_handle_msg(msg))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    # Shutdown: wait for remaining tasks to complete
    if pending_tasks:
        logging.info(f"Waiting for {len(pending_tasks)} pending tasks to complete...")
        await asyncio.gather(*pending_tasks, return_exceptions=True)

    _consumer.close()
    logging.info("Consumer loop closed.")

def stop_consumer():
    global _running
    _running = False
