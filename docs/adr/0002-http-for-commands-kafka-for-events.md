---
status: accepted
date: 2026-10-26
decision-makers: Andriy
---

# ADR-002: HTTP for commands and queries, Kafka for domain events

## Context and Problem Statement

Services have to talk to each other in two different ways. During checkout, Orders needs an immediate answer from Inventory and Payments before it can decide the next saga step. In other cases a service only announces a fact (a shipment was dispatched) and must not care who reacts, or whether they are available right now (NFR-05).

Which communication style is used for which kind of interaction?

## Decision Drivers

- Saga steps need a direct, typed answer and clear timeouts (NFR-06).
- Billing, Catalog and forecasting must be able to fail without blocking checkout (NFR-05).
- Events of one order or stock item must be processed in order (NFR-02, NFR-03).
- The system must start on one machine with free tools (NFR-15, C-03).

## Considered Options

1. HTTP for commands and queries, Kafka for domain events.
2. Kafka for everything, including commands and replies.
3. HTTP for everything, with events delivered as webhook calls.

## Decision Outcome

Chosen option: **1. HTTP for commands and queries, Kafka for domain events**.

- Commands and queries between services use HTTP under `/internal/v1/...`. The gateway does not route these paths. Public API is `/api/v1/...` behind the gateway.
- Facts are published as versioned events on one Kafka topic per producing context, keyed by aggregate ID, with the envelope defined in `docs/api/asyncapi.yaml`.
- Events carry everything a consumer needs (event-carried state transfer), so Billing and Catalog never call back into Orders or Inventory.

### Consequences

- Good: saga steps are simple request and response calls that can be retried and traced.
- Good: consumers are decoupled in time, so an outage of Billing only delays invoices until it recovers (NFR-05).
- Bad: two mechanisms and two contract formats, OpenAPI for HTTP and AsyncAPI for events.
- Bad: HTTP calls need timeouts, retries with backoff and circuit breakers (NFR-06), and events need the outbox and inbox (ADR-005).
- Bad: no single transaction spans an HTTP call and an event, so consistency relies on the saga (ADR-003).

### Confirmation

- Contract tests check each service against its OpenAPI file and event payloads against the AsyncAPI schemas.
- Failure tests stop a consumer and a Kafka broker and check that APIs keep working and events are delivered after recovery (NFR-03, NFR-05).

## Pros and Cons of the Options

### 1. HTTP for commands, Kafka for events

- Good, because each mechanism is used where it fits: answers where an answer is needed, facts where coupling must be loose.
- Bad, because two mechanisms have to be learned, tested and operated.

### 2. Kafka for everything

- Good, because there is one mechanism and one contract format.
- Bad, because request and reply over a log makes saga steps and their timeouts harder to read, test and debug.

### 3. HTTP for everything

- Good, because there is only one mechanism and no broker to run.
- Bad, because a producer would depend on the availability of every consumer, which breaks NFR-05.

## More Information

PRD: NFR-02, NFR-03, NFR-05, NFR-06. TRD: "Interfaces", "Event catalogue", "Checkout saga".
