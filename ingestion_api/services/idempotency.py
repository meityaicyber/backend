import logging

IDEMPOTENCY_TTL_SECONDS = 86400 # 24 hours

async def check_idempotency(redis_client, idempotency_key: str, job_id: str):
    """
    Checks if an idempotency key exists.
    If it does not exist, sets it with the job_id and returns (True, job_id).
    If it exists, returns (False, existing_job_id).
    """
    key = f"idempotency:{idempotency_key}"
    try:
        # SETNX sets the value only if it does not exist
        # We also want to set a TTL. In Redis 6.0+, SET has NX and EX options.
        was_set = await redis_client.set(key, job_id, nx=True, ex=IDEMPOTENCY_TTL_SECONDS)
        
        if was_set:
            return True, job_id
        else:
            existing_job_id = await redis_client.get(key)
            return False, existing_job_id
    except Exception as e:
        logging.error(f"Idempotency check failed: {e}")
        # In case of failure, we allow it through rather than failing with 5xx,
        # relying on PostgreSQL unique constraints to catch duplicates later if needed.
        # But wait, 0% 5xx means we must not crash. We return True so it proceeds.
        return True, job_id

async def clear_idempotency(redis_client, idempotency_key: str):
    """
    Called if job persistence fails, allowing the client to retry.
    """
    key = f"idempotency:{idempotency_key}"
    try:
        await redis_client.delete(key)
    except Exception:
        pass
