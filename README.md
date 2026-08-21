# Cyber Audit High-Throughput Ingestion Pipeline

This project implements an AI-Based Solution for Analysing, Benchmarking and Quality Monitoring of Cybersecurity Audit Reports. 
It specifically addresses the requirement for a High-Throughput Document Ingestion & Processing Pipeline.

## Architecture

The system is designed as an asynchronous, event-driven pipeline:
1. **Ingestion API (FastAPI):** Receives multipart document uploads. Uses Uvicorn concurrency limits and Redis-backed admission control to achieve 0% 5xx errors under load.
2. **Idempotency Layer (Redis):** Caches `Idempotency-Key` headers to ensure duplicate uploads are gracefully ignored and return the existing Job ID.
3. **Message Broker (Redpanda/Kafka):** Buffers the burst of uploads. Uses `agency_id` as the partition key to guarantee chronological ordering of documents from the same agency.
4. **Worker Nodes (Python/asyncio):** Consume messages from Kafka, simulate heavy processing, and provide *At-Least-Once Delivery* by committing Kafka offsets only after successful PostgreSQL transactions.
5. **Observability (Prometheus/Grafana):** Fully instrumented to visualize API throughput, 429 rejection rates, latency, and worker performance.

## Capacity Guarantees

Based on the 12-core, 16GB reference hardware:
* **Max Active Pipelines:** 2,500
* **Target Processing Rate:** 166.67 documents/second
* **Burst Limit:** The API is designed to handle 5,000 uploads in 30 seconds by gracefully rejecting excess traffic (HTTP 429 Retry-After) rather than crashing (HTTP 500).

## Quickstart (Offline Local Deployment)

Everything runs locally via Docker Compose. No cloud dependencies are required.

1. **Boot the Cluster:**
   ```bash
   docker compose up -d --build
   ```
   *This starts Redpanda, Redis, PostgreSQL, Prometheus, Grafana, the Ingestion API, and 4 Worker replicas.*

2. **Verify Services:**
   Check that all containers are healthy.
   ```bash
   docker compose ps
   ```

3. **Access Dashboards:**
   * **Grafana:** `http://localhost:3000` (Default credentials, pre-provisioned dashboards)
   * **API Docs:** `http://localhost:8080/docs`

## Load Testing

A Locust test suite is provided to validate the 5,000 document burst scenario.

1. **Install Dependencies:**
   ```bash
   cd load_tests
   pip install -r requirements.txt
   ```

2. **Run the Load Test:**
   ```bash
   locust -f locustfile.py --host=http://localhost:8080
   ```
   Open `http://localhost:8089` to configure the test (e.g., 5,000 users, 500 spawn rate).
   *Expect to see a mix of 202 (Accepted) and 429 (Too Many Requests). You should see exactly **0** 500-level errors.*

## Design Documentation

For deep dives into the architectural contracts, please refer to:
* `docs/design/architecture.md`
* `docs/design/capacity-model.md`
* `docs/design/sharding-contract.md`
* `docs/design/datastore-contract.md`