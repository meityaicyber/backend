# Mathematical Capacity Model

## 1. Reference Hardware
* CPU Model/Core Count: 12th Gen Intel(R) Core(TM) i7-12700 (12 Physical Cores, 20 Logical Processors)
* RAM: ~16 GB (16,475,768 KB visible)
* OS: Windows (Running Docker Desktop Linux Containers)

## 2. Arrival Rate & Targets
* Burst Submissions: 5,000 documents
* Burst Window: 30 seconds
* **Required Arrival Rate:** 166.67 documents/second
* **Active Pipelines Target:** 2,500 concurrent pipelines
* **API Latency Target:** p95 < 150ms

## 3. Capacity Derivations

### Kafka Partitions
* **Parameter:** `num_partitions = 100`
* **Source:** Derived / Judgement Call
* **Calculation/Reasoning:** To support 2,500 active pipelines concurrently, assigning 2,500 Kafka partitions (1 per worker thread) would cause high broker overhead and rebalancing storms. Instead, we use 100 partitions. This allows up to 100 consumer processes. Each consumer process will internally use async I/O to manage up to 25 concurrent pipelines (100 processes * 25 pipelines = 2,500 concurrent pipelines).
* **Validation Method:** Benchmark consumer lag and active worker count during load test.

### Ingestion API Concurrency Limit
* **Parameter:** `limit_concurrency = 200`
* **Source:** Derived
* **Calculation/Reasoning:** Using Little's Law ($L = \lambda W$): For an expected spike $\lambda$ of up to 500 requests/sec, and a target latency $W = 0.15$ seconds, the average concurrent requests $L = 75$. Setting the hard limit to 200 across the API tier provides headroom for transient spikes without risking resource exhaustion or 5xx errors. Exceeding this triggers a 429 response.
* **Validation Method:** Burst load test observing 0% 5xx errors and successful HTTP 429 shedding.

### Worker Node Limits
* **Parameter:** `worker_containers = 4`
* **Source:** Judgement Call
* **Calculation/Reasoning:** The reference hardware has 12 physical cores. 4 worker containers balance CPU scheduling gracefully, leaving cores available for Kafka, Redis, PostgreSQL, and the API.
* **Parameter:** `worker_memory_limit = 2 GB`
* **Source:** Derived
* **Calculation/Reasoning:** Each worker handles 25 concurrent async pipelines. Assuming an average of 40MB memory overhead for document parsing per pipeline, $25 \times 40\text{MB} = 1,000\text{MB}$. A 2GB limit provides a 100% buffer for garbage collection and runtime overhead.

### Ingestion API Limits
* **Parameter:** `api_memory_limit = 512 MB`
* **Source:** Derived
* **Calculation/Reasoning:** The API performs payload validation, Redis idempotency checks, and Kafka message production. It is highly I/O bound. A 512MB limit is more than sufficient for 200 concurrent network connections.

### Redis Memory Budget
* **Parameter:** `maxmemory = 256mb`
* **Source:** Derived
* **Calculation/Reasoning:** Used primarily for `Idempotency-Key` storage and rate-limit counters. A single key-value pair takes $\approx 1$ KB. 5,000 requests require $\approx 5$ MB. 256MB provides vast headroom for bursts, cache fragmentation, and Redis overhead.
* **Validation Method:** Monitor Redis `used_memory` metrics during the 5,000 document load test.
