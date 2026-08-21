import asyncio
import logging
from database import get_job_status, update_job_status, complete_job_transaction
import redis.asyncio as redis
import os
import time
from prometheus_client import Counter, Histogram

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis_client = None

JOBS_PROCESSED = Counter('worker_jobs_processed_total', 'Total jobs processed', ['status'])
PROCESSING_TIME = Histogram('worker_processing_duration_seconds', 'Processing duration')

async def init_redis():
    global _redis_client
    _redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def close_redis():
    if _redis_client:
        await _redis_client.close()

async def process_document(payload: dict) -> bool:
    """
    Processes a single document event.
    Returns True if successfully processed (so caller can ACK Kafka).
    Returns False if processing failed but should NOT be acked (so it retries).
    """
    job_id = payload.get("job_id")
    if not job_id:
        logging.error("Invalid payload: missing job_id")
        return True # Ack and drop invalid messages

    start_time = time.time()
    try:
        # 1. At-Least-Once Delivery Idempotency Check
        current_status = await get_job_status(job_id)
        if current_status in ["COMPLETED", "FAILED"]:
            logging.info(f"Job {job_id} already in terminal state ({current_status}). Skipping.")
            return True # Ack to skip

        # 2. Update status to PROCESSING
        await update_job_status(job_id, "PROCESSING")

        # 3. Simulate Heavy Processing (Extraction, Parsing, Analytics)
        # In real life, we would call AI_PIPELINE_URL here.
        await asyncio.sleep(0.5) # Simulate latency

        # 4. Save results in DB Transaction (Source of Truth)
        fake_results = {"extracted_text": "Sample text", "score": 95}
        await complete_job_transaction(job_id, fake_results)
        
        # 5. Decrement active_pipelines metric in Redis to free up ingestion capacity
        if _redis_client:
            try:
                await _redis_client.decr("active_pipelines")
            except Exception:
                pass # Redis failure shouldn't fail the pipeline at this stage

        
        JOBS_PROCESSED.labels(status='success').inc()
        return True # Everything succeeded, safe to ACK
        
    except Exception as e:
        logging.error(f"Processing failed for job {job_id}: {e}")
        # If DB is down or extraction failed, return False.
        # Kafka consumer will NOT commit offset, so the message is redelivered.
        JOBS_PROCESSED.labels(status='failed').inc()
        return False
    finally:
        PROCESSING_TIME.observe(time.time() - start_time)
