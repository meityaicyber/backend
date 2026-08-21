import os
import redis.asyncio as redis
from confluent_kafka import Producer
import asyncpg

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/cyber_audit")

# Global clients to reuse connections
_redis_client = None
_kafka_producer = None
_db_pool = None

async def init_dependencies():
    global _redis_client, _kafka_producer, _db_pool
    if not _redis_client:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    if not _kafka_producer:
        _kafka_producer = Producer({"bootstrap.servers": KAFKA_BROKER})
    if not _db_pool:
        # For simplicity and testing without full DB, we allow this to fail gracefully or mock it in tests
        try:
            _db_pool = await asyncpg.create_pool(DATABASE_URL)
        except Exception as e:
            print(f"Warning: DB connection failed: {e}")

async def close_dependencies():
    if _redis_client:
        await _redis_client.close()
    if _kafka_producer:
        _kafka_producer.flush(timeout=5)
    if _db_pool:
        await _db_pool.close()

async def get_redis():
    if not _redis_client:
        await init_dependencies()
    return _redis_client

def get_kafka_producer():
    # Producer is synchronous in confluent_kafka, but we initialize it in init_dependencies
    return _kafka_producer

async def get_db():
    if not _db_pool:
        await init_dependencies()
    return _db_pool
