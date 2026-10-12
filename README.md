# clothes-order-management-system

Order Management System for a fashion retail network (warehouses + stores), built in Python, with demand forecasting that improves where orders are shipped from.

STATUS: PLANNED

## About

The project consists of an e-commerce backend (REST API, no frontend) for a clothing retailer that ships online orders from several locations: central warehouses and physical stores. Besides the standard e-commerce domains (customers, products, orders, payments, invoices), the project focuses on the part most shops handle poorly: knowing where each item physically is, reserving it safely, and deciding where to ship it from. A demand-forecasting component predicts how fast each item will sell at each location, so that this decision takes expected future sales into account.

## Problem

- Fashion has many variants per product (size x colour), so one popular size can sell out in minutes while other locations still hold it.
- Concurrent orders can sell the same last item twice (overselling).
- A basket of several items may be available in different locations, so the system must choose between one slow/expensive parcel and several fast ones.
- The nearest or cheapest location is not always the best one: shipping the last unit of a size from a store that is about to sell it in person costs a sale there.
- Payment and stock must stay consistent when a service or a payment provider fails mid-order.

## Target users

- **Customers**: browse the catalogue, place and track orders.
- **Retail operations**: monitor stock per location, predicted demand, shipments and order states.
- **Finance**: receive correct invoices per shipment and corrections after returns.

## Core idea

An order is processed as a chain of events across independent services:

1. **Orders** accepts the order (idempotent) and starts a **saga** (a chain of local steps with compensating actions on failure).
2. **Inventory** builds an allocation plan (which item from which location) using a replaceable allocation strategy, then atomically reserves stock with a TTL. Strategies can use demand forecasts (see below).
3. **Payments** authorises the amount. On failure the saga compensates and releases the reservation.
4. The order is split into one or more **shipments**; per shipment the payment is captured and **Billing** issues an invoice.

Services communicate over HTTP (synchronous queries and commands) and Kafka (domain events). A transactional outbox guarantees that a state change and its event are never out of sync.

### Demand forecasting

- **What it predicts:** expected sales per item variant (size x colour) and location for the coming days.
- **How it is used:** as one term in the allocation cost, next to shipping cost, extra-parcel penalty and SLA: the risk of losing a sale at the location the unit is taken from.
- **How it is built:** an offline pipeline (historical sales, features, gradient boosting) produces a versioned model, and a scheduled job stores forecasts in Inventory's database. Order processing therefore never waits for the model.
- **Fallback:** if forecasts are missing or stale, allocation falls back to a simple moving average of recent sales. The core flow (reserve, pay, ship, invoice) does not depend on the forecast.

## Planned architecture

| Service   | Domain            | Responsibility                                                                                    |
| --------- | ----------------- | ------------------------------------------------------------------------------------------------- |
| Customers | Customers         | Registration, login (JWT), profile, addresses                                                     |
| Catalog   | Products          | Products, variants (size/colour), prices, categories, search                                      |
| Orders    | Orders            | Cart, checkout, order life cycle, shipments (mock carrier), saga orchestration                    |
| Inventory | Products (stock)  | Stock per location, reservations with TTL, allocation strategies (incl. forecast-aware), stored demand forecasts |
| Payments  | Payments          | Authorise / capture / refund via a mock payment provider                                          |
| Billing   | Invoices/Receipts | Invoice per shipment, VAT, receipt, correction document                                           |

Each service uses hexagonal architecture (ports and adapters). Calls to the payment provider and between services are protected by Circuit Breaker and Retry, and requests are traced end to end. Demand forecasting is not a seventh service: it is a module of Inventory plus an offline training job.

## Planned stack

Python, FastAPI, PostgreSQL, Kafka, pytest, Testcontainers, Docker Compose. Forecasting: pandas, scikit-learn, LightGBM. All tools are free to use and run locally.

## Forecasting evaluation plan

**Hypothesis (to be tested, not assumed):** allocation that accounts for expected demand loses fewer sales and costs less than rule-based allocation.

- **Data:** public retail sales datasets for training and evaluating the forecaster (candidates: H&M Personalized Fashion Recommendations, M5). The location network, stock and orders are simulated. Datasets are not stored in the repository and are used under their licence terms.
- **Forecast quality:** error (WAPE/MAE) against naive baselines (same as last week, moving average).
- **Allocation:** a simulator runs the same allocation code as the service and compares: nearest location, cheapest, fewest parcels, naive-forecast-aware, ML-forecast-aware, and an "oracle" with perfect knowledge of future demand (upper bound).
- **Metrics:** order fill rate, lost sales, cost per order, parcels per order, SLA compliance. Repeated runs with different random seeds and confidence intervals.

## How the project meets the course requirements

### Grading components

| Grade | Requirement | How it is met | Status |
|---|---|---|---|
| 3.0 | Web service | REST API per service with OpenAPI/Swagger | Planned |
| 3.5 | + Unit tests | Pure domain logic (state machines, reservation rules, allocation strategies with and without forecasts, forecast fallback, VAT calculation) covered by pytest without I/O | Planned |
| 4.0 | + Integration tests + design patterns | Integration tests against real PostgreSQL and Kafka (Testcontainers). Patterns: Strategy (allocation, forecast-aware or not), State (order life cycle), Specification (location eligibility), Adapter (payment provider, mock carrier, forecaster), Saga, Outbox | Planned |
| 4.5 | + Microservices + inter-service communication | Six independently runnable services; HTTP between services and Kafka events | Planned |
| 5.0 | + Documentation | README, OpenAPI specs, C4 diagrams, ADRs, setup and test instructions | Planned |

Demand forecasting is an extension beyond the graded components: it is built after the core, sits behind a port with a fallback, and no grade level depends on it.

### API requirements

| Requirement | Coverage |
|---|---|
| Services necessary for e-commerce | Authentication, catalogue browsing and search, cart, checkout, order tracking, shipments |
| **Customers** | Register, log in, edit profile, manage delivery addresses |
| **Products** | Product and variant CRUD, prices, categories, per-location stock |
| **Orders** | Add to cart, place order (idempotency key), history, cancellation, split shipments, statuses |
| **Payments** | Authorise, capture per shipment, refund, payment status |
| **Invoices/Receipts** | Invoice per shipment with VAT, receipt, correction invoice after a return or cancellation |
| Demand forecast (extension) | Read predicted demand and stockout risk per item variant and location; used internally by allocation |
| Key functionalities within the domains | The functions above are the working definition; to be confirmed with the instructor |
