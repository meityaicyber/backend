import os
import asyncpg
import logging

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:supersecretpassword@localhost:5432/cyber_audit")

_db_pool = None

async def init_db():
    global _db_pool
    try:
        _db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    except Exception as e:
        logging.error(f"Failed to initialize DB pool: {e}")

async def close_db():
    if _db_pool:
        await _db_pool.close()

async def get_job_status(job_id: str) -> str:
    if not _db_pool:
        return None
    async with _db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT status FROM jobs WHERE job_id = $1", job_id)
        return result

async def update_job_status(job_id: str, status: str):
    if not _db_pool:
        return
    async with _db_pool.acquire() as conn:
        await conn.execute("UPDATE jobs SET status = $1, updated_at = NOW() WHERE job_id = $2", status, job_id)

async def complete_job_transaction(job_id: str, results: dict):
    """
    Simulates saving final extracted data and completing the job in a single transaction.
    """
    if not _db_pool:
        return
    async with _db_pool.acquire() as conn:
        async with conn.transaction():
            # 1. Update job to COMPLETED
            await conn.execute(
                "UPDATE jobs SET status = 'COMPLETED', completed_at = NOW() WHERE job_id = $1",
                job_id
            )
            # 2. Insert results (using a generic report_metadata table assumption)
            # For this exercise, we just succeed if the transaction doesn't throw.
            pass
