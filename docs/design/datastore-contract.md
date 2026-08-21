# Data Ownership and Data-Store Contract

This contract defines the explicit roles, boundaries, and eviction policies for each stateful service in the pipeline.

## 1. PostgreSQL (The Source of Truth)

**Role:** The durable, highly available source of truth for all jobs, processing states, metadata, and extracted results.

**Contract Guarantees:**
* **Durable State:** A job is only considered logically created when the `status = ACCEPTED` record is committed here.
* **Terminal State:** A job is only considered finished when `status = COMPLETED` or `FAILED` is successfully committed.
* **At-Least-Once Safety:** Worker nodes **must not** acknowledge a Kafka offset until the PostgreSQL transaction committing the terminal state and the parsed results succeeds. 

**Persisted Entities (Minimum):**
* `job_id` (Primary Key, UUID)
* `document_id`
* `agency_id`
* `case_id`
* `status` (ACCEPTED, QUEUED, PROCESSING, COMPLETED, FAILED, REJECTED)
* `timestamps` (created_at, updated_at, completed_at)
* `error_details` (if applicable)

## 2. Redis (Idempotency and Admission)

**Role:** Ephemeral, high-speed layer for caching `Idempotency-Key`s, tracking admission metrics (e.g., active processing slots), and rate limiting.

**Contract Guarantees & Configuration:**
* **Not a Durable Queue:** Redis must never be treated as a durable queue. If Redis data is lost, correctness must still be recoverable via PostgreSQL constraints (e.g., unique indices on idempotency keys).
* **Eviction Policy:** `volatile-ttl`. Redis will only evict keys that have a TTL set, ensuring it does not silently drop persistent state if misused.
* **TTL Definitions:**
  * `Idempotency-Key`: 24 hours.
  * Rate limit / active pipeline counters: Expire within seconds/minutes depending on the metric window.
* **Memory Budget:** Capped at 256MB. 

## 3. Kafka / Redpanda (Asynchronous Buffer)

**Role:** The durable event broker responsible for buffering ingestion bursts, decoupling the API from workers, and handling partition distribution.

**Contract Guarantees:**
* **Burst Buffering:** Kafka's disk-backed log absorbs the 166.67 docs/sec burst without blocking the HTTP API.
* **At-Least-Once Delivery:** Kafka relies on manual consumer offset commits. If a worker crashes mid-processing, Kafka will redeliver the event.
* **Not the Source of Truth:** Kafka does not hold the final status of a document. It only holds the command/event to process it.
