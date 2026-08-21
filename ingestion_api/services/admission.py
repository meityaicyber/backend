from fastapi import HTTPException
import logging

MAX_ACTIVE_PIPELINES = 2500

async def check_admission(redis_client):
    """
    Checks if the system has capacity to accept a new job.
    Returns True if admitted, raises HTTPException(429) if rejected.
    """
    try:
        # In a real system, workers decrement this counter when a job reaches a terminal state.
        # For admission control, we check if it exceeds the limit.
        active = await redis_client.get("active_pipelines")
        active = int(active) if active else 0

        if active >= MAX_ACTIVE_PIPELINES:
            # We must return HTTP 429 Retry-After when overloaded
            raise HTTPException(
                status_code=429,
                detail="System at maximum capacity",
                headers={"Retry-After": "5"}
            )
        
        # Optimistically increment. If it fails later, it will be decremented or TTL will clear it.
        await redis_client.incr("active_pipelines")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Admission control error: {e}")
        # Fail open? No, fail closed under load, but since we require 0% 5xx, we should
        # handle redis failures gracefully. If Redis is down, we fallback to 429.
        raise HTTPException(
            status_code=429,
            detail="Service temporarily degraded",
            headers={"Retry-After": "10"}
        )
