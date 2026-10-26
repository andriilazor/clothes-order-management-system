---
status: accepted
date: 2026-10-26
decision-makers: Andriy
---

# ADR-005: Transactional outbox and inbox in every service

## Context and Problem Statement

A service changes its own state and then announces the fact as an event. If it writes to the database and then publishes to Kafka, a crash between the two leaves an event that was lost or a state change nobody heard about (NFR-03). Kafka also delivers at least once, so a consumer can see the same event twice and must not act twice (NFR-02).

How do state changes and events stay together, and how do consumers stay idempotent?

## Decision Drivers

- A state change and the event that announces it are never separated: neither lost, neither alone (NFR-03).
- Processing any message twice has the same effect as once (NFR-02).
- Correctness without extra infrastructure on one developer machine (C-01, C-03).
- One shared implementation instead of six slightly different ones (TR-02).

## Considered Options

1. Transactional outbox in the producer and inbox in the consumer.
2. Dual write: change the database, then publish to Kafka from business code.
3. Change data capture from the database log with Debezium.

## Decision Outcome

Chosen option: **1. Transactional outbox and inbox in every service**.

- **Outbox.** Business code writes the event to the service's `outbox` table in the same database transaction as the state change. It never publishes to Kafka directly. A relay process reads unsent rows with `FOR UPDATE SKIP LOCKED`, publishes them keyed by aggregate ID, and marks them sent. Delivery is at least once.
- **Inbox.** A consumer inserts the `event_id` into its `inbox` table in the same transaction as its own change. A duplicate insert means the event was already handled and is skipped. Offsets are committed after the transaction.
- Both live in the shared library `libs/platform` and are not copied into services.
- Trace context is written into Kafka headers by the relay and restored by consumers (NFR-08).

### Consequences

- Good: a state change and its event are atomic, with no extra component beyond Kafka and PostgreSQL.
- Good: duplicate delivery is harmless, so relays and consumers can simply retry.
- Bad: events appear after a polling delay, not instantly.
- Bad: the relay and inbox are subtle and shared by all services, so a bug affects all of them. They get their own integration tests (TR-02).
- Bad: outbox and inbox rows accumulate. A retention policy is not decided yet and must be set before R2.

### Confirmation

- Integration tests on real PostgreSQL and Kafka: kill the relay between publish and mark-as-sent and check that the event is delivered and handled exactly once in effect.
- Every consumer has a duplicate-delivery test.
- An import-linter contract forbids Kafka clients in `domain`, and the layer contract lets `application` reach adapters only through ports, so business code cannot publish directly.

## Pros and Cons of the Options

### 1. Outbox and inbox

- Good, because atomicity comes from the database transaction the service already has.
- Bad, because it adds two tables per service and a relay process.

### 2. Dual write

- Good, because it is the simplest to write.
- Bad, because a crash between the two writes loses an event or announces a state that was never saved, which is what NFR-03 forbids.

### 3. Change data capture (Debezium)

- Good, because services need no relay code and capture is reliable.
- Bad, because it adds Kafka Connect and a connector to run and configure, which no driver justifies on one machine.

## More Information

PRD: NFR-02, NFR-03, NFR-08. TRD: "Consistency and resilience", "Event catalogue" (envelope), TR-02.
