---
status: accepted
date: 2026-10-26
decision-makers: Andriy
---

# ADR-001: Six microservices, database per service

## Context and Problem Statement

The system covers six domains: customers, catalogue, stock, orders, payments and invoicing. Checkout touches most of them, and a failure in one part (a slow payment provider, a down invoicing component) must not stop the rest (NFR-05). The course also grades independently running services that cooperate through inter-service communication (grade 4.5). The system is built by one person on one machine (C-01, C-03).

How should the system be split into deployable units, and who owns the data?

## Decision Drivers

- Failure isolation: checkout and shipping continue when invoicing or forecasting is down (NFR-05).
- Replaceable parts: payment provider, carrier, allocation strategy and forecaster can change without touching order processing (NFR-14).
- Course grade 4.5: microservices and inter-service communication.
- One developer and one laptop: no infrastructure that no driver needs (C-01, C-03, TR-04).

## Considered Options

1. Six microservices (Customers, Catalog, Inventory, Orders, Payments, Billing), each with its own database.
2. Modular monolith with one database and module boundaries.
3. Six services sharing one database schema.

## Decision Outcome

Chosen option: **1. Six microservices, database per service**, because it is the only option that satisfies failure isolation and the course requirement at the same time.

- Each service owns its data and is its only reader and writer. Other services reach that data through its API or its events; there are no shared tables and no cross-database queries.
- Locally the six databases live on one PostgreSQL server, each with its own credentials, so a service can reach only its own database while the laptop footprint stays small.
- Shipments stay inside Orders and forecasting stays a module of Inventory, which keeps the count at six (see ADR-007 and ADR-012).

### Consequences

- Good: a service can fail, restart or be replaced without stopping the others (NFR-04, NFR-05, NFR-14).
- Good: data ownership is enforced by credentials, not only by convention.
- Bad: consistency across services needs a saga, an outbox and idempotent consumers (ADR-003, ADR-005), which is the largest technical risk (TR-01, TR-02).
- Bad: more moving parts to run on one machine. Memory is measured in R0 against the 6 GB target (TR-04, TQ-02).
- Bad: more work for one developer, mitigated by a shared platform library (ADR-009) and strict release order (RSK-01).

### Confirmation

- An independence contract in import-linter keeps services from importing each other; it is added when the second service is created. The shared library must not import any service (already in place).
- Each service connects with credentials that open only its own database; verified in integration tests against real PostgreSQL.
- Failure tests stop Billing, then Payments, and check that the behaviour in the TRD "Failure behaviour by component" table holds (NFR-05).

## Pros and Cons of the Options

### 1. Six microservices, database per service

- Good, because failures stay local and data ownership is enforceable.
- Good, because it meets the 4.5 grading component.
- Bad, because of distributed-system complexity and a heavier local environment.

### 2. Modular monolith

- Good, because it has the fewest moving parts and no distributed consistency problem.
- Bad, because a fault in one module can take the whole process down, so NFR-05 is only simulated.
- Bad, because it does not meet the 4.5 grading component.

### 3. Six services sharing one schema

- Good, because transactions across services are possible.
- Bad, because shared tables couple the services and remove the isolation that justifies splitting them.

## More Information

PRD: NFR-04, NFR-05, NFR-14, C-01, C-03, grade 4.5 in "Course requirements mapping". TRD: "Architectural drivers", "System architecture", TR-04.
