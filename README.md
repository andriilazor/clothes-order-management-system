# clothes-order-management-system

Order Management System for a fashion retail network (warehouses + stores), built in Python.

STATUS: PLANNED

## About

The project consists of an e-commerce backend (REST API, no frontend) for a clothing retailer that ships online orders from several locations: central warehouses and physical stores. Besides the standard e-commerce domains (customers, products, orders, payments, invoices), the project focuses on the part most shops handle poorly: knowing where each item physically is, reserving it safely, and deciding where to ship it from.

## Problem

- Fashion has many variants per product (size x colour), so one popular size can sell out in minutes while other locations still hold it.
- Concurrent orders can sell the same last item twice (overselling).
- A basket of several items may be available in different locations, so the system must choose between one slow/expensive parcel and several fast ones.
- Payment and stock must stay consistent when a service or a payment provider fails mid-order.

## Target users

- **Customers**: browse the catalogue, place and track orders.
- **Retail operations**: monitor stock per location, shipments and order states.
- **Finance**: receive correct invoices per shipment and corrections after returns.

## Core idea

An order is processed as a chain of events across independent services:

1. **Orders** accepts the order (idempotent) and starts a **saga**.
2. **Inventory** builds an allocation plan (which item from which location) using a replaceable allocation strategy, then atomically reserves stock with a TTL.
3. **Payments** authorises the amount. On failure the saga compensates and releases the reservation.
4. The order is split into one or more **shipments**; per shipment the payment is captured and **Billing** issues an invoice.

Services communicate over HTTP (synchronous queries and commands) and Kafka (domain events). A transactional outbox guarantees that a state change and its event are never out of sync.

## Planned architecture

| Service   | Domain            | Responsibility                                                   |
| --------- | ----------------- | ---------------------------------------------------------------- |
| Customers | Customers         | Registration, login (JWT), profile, addresses                    |
| Catalog   | Products          | Products, variants (size/colour), prices, categories, search     |
| Orders    | Orders            | Cart, checkout, order life cycle, shipments, saga orchestration  |
| Inventory | Products (stock)  | Stock per location, reservations with TTL, allocation strategies |
| Payments  | Payments          | Authorise / capture / refund via a mock payment provider         |
| Billing   | Invoices/Receipts | Invoice per shipment, VAT, receipt, correction document          |

## How the project meets the course requirements

### Grading components

| Grade | Requirement | How it is met | Status |
|---|---|---|---|
| 3.0 | Web service | REST API per service with OpenAPI/Swagger | Planned |
| 3.5 | + Unit tests | Pure domain logic (state machines, reservation rules, allocation strategies, VAT calculation) covered by pytest without I/O | Planned |
| 4.0 | + Integration tests + design patterns | Integration tests against real PostgreSQL and Kafka (Testcontainers). Patterns: Strategy (allocation), State (order life cycle), Specification (location eligibility), Adapter (payment provider, carriers), Saga, Outbox | Planned |
| 4.5 | + Microservices + inter-service communication | Six independently runnable services; HTTP between services and Kafka events | Planned |
| 5.0 | + Documentation | README, OpenAPI specs, C4 diagrams, ADRs, setup and test instructions | Planned |

### API requirements

| Requirement | Coverage |
|---|---|
| Services necessary for e-commerce | Authentication, catalogue browsing and search, cart, checkout, order tracking, shipments |
| **Customers** | Register, log in, edit profile, manage delivery addresses |
| **Products** | Product and variant CRUD, prices, categories, per-location stock |
| **Orders** | Add to cart, place order (idempotency key), history, cancellation, split shipments, statuses |
| **Payments** | Authorise, capture per shipment, refund, payment status |
| **Invoices/Receipts** | Invoice per shipment with VAT, receipt, correction invoice after a return or cancellation |
| Key functionalities within the domains | The functions above are the working definition; to be confirmed with the instructor |
