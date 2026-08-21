# Sharding and Partitioning Contract

## 1. Routing Definition

**Partition Key:** `agency_id`

All incoming document submissions must be routed to Kafka/Redpanda using the `agency_id` as the message key.

## 2. Invariants

The system guarantees the following under normal operation:
1. **Partition Locality:** All documents submitted for the same `agency_id` will be routed to the exact same Kafka partition.
2. **Strict Ordering:** Documents within the same partition (and therefore the same agency) will be processed by consumers in the exact order they were enqueued by the Ingestion API.
3. **Concurrent Execution:** Documents from *different* agencies may be routed to different partitions and processed concurrently.
4. **Deterministic Assignment:** The partition assignment relies on a deterministic hash of the partition key (`hash(agency_id) % num_partitions`).

## 3. Partition Scaling Constraint (DANGER)

> [!WARNING]
> **Partition Counts are Immutable on the Active Topic.**

The number of Kafka partitions on the ingestion topic is **strictly fixed** (e.g., to 100).

**What breaks when partition count changes?**
Because partition assignment is determined by `hash(agency_id) % num_partitions`, changing the denominator (`num_partitions`) changes the resulting partition index for almost all existing `agency_id`s.

If the partition count is increased on a live topic:
1. Newly ingested documents for an agency may be routed to a *new* partition.
2. The consumer for the *new* partition may process the new document **before** the consumer for the *old* partition finishes processing the older documents in the backlog.
3. **The Strict Ordering invariant is violated.**

**Approved Migration Strategy:**
To scale partitions, the system must NOT alter the active topic. Instead:
1. Create a new topic `ingestion_v2` with the new partition count.
2. The API routes new requests to `ingestion_v2`.
3. Workers consume from both `ingestion_v1` and `ingestion_v2`, but prioritize draining `ingestion_v1`.
4. Once `ingestion_v1` is completely empty, it can be decommissioned.
