import json
import logging

def publish_event(producer, topic: str, partition_key: str, payload: dict):
    """
    Publishes an event to Kafka using the agency_id as the partition key.
    This guarantees ordering for documents from the same agency.
    """
    try:
        # We must serialize the payload to bytes
        value = json.dumps(payload).encode("utf-8")
        key = partition_key.encode("utf-8")
        
        producer.produce(
            topic=topic,
            key=key,
            value=value
        )
        producer.poll(0) # trigger delivery reports
    except BufferError:
        # Producer queue is full (backpressure)
        raise BufferError("Kafka producer queue full")
    except Exception as e:
        logging.error(f"Failed to publish to Kafka: {e}")
        raise
