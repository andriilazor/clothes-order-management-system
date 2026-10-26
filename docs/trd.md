# TRD — Clothes Order Management System

Oct 26, 2026 · @Andriy

## Document control

This TRD describes how the system satisfies PRD version 0.2; every design element names the PRD IDs it serves. Where the PRD leaves a question open, the TRD states a design default and marks it as such.

| Field | Value |
| --- | --- |
| Document | Technical Requirements Document (TRD) |
| Version | 0.3 (draft) |
| Baseline | PRD v0.2 (minimal web frontend, FR-WEB-01–06) |
| IDs used | PRD IDs (FR, NFR, BR, US, Q); ADR-NN decision records; TQ-NN open technical questions; TR-NN technical risks |
| Reading order | Drivers → domain → architecture → flows → data → quality → plan |

| Version | Date | Change |
| --- | --- | --- |
| 0.3 | 2026-10-26 | docs/ moved into the repository; contract tests back in CI; TQ-07 resolved |
| 0.2 | 2026-10-26 | Workspace layout: documents and knowledge base live beside the repository in COMS/ and are not committed; only the developer commits and pushes; TQ-07 added |
| 0.1 | 2026-10-26 | First draft from PRD v0.2 and the project README |

## PRD alignment

PRD v0.2 adds a minimal web frontend, and the inconsistencies this raised in v0.1 are resolved there; the TRD designs the frontend as a thin client of the public API.

| Change in PRD v0.2 | Where this TRD answers it |
| --- | --- |
| Overview and Non-goals: minimal required frontend | Web app container in System architecture; Minimal frontend section |
| New domain WEB, FR-WEB-01–06 | Screen list in Minimal frontend; Implementation plan R1–R3 |
| C-04: every function reachable through the API; frontend holds no business logic | Web app calls the gateway like any other client; ADR-010 |
| Release scope includes FR-WEB | Implementation plan |

Open PRD questions that block design get a design default, which the PRD answer may overturn.

| PRD question | Design default |
| --- | --- |
| Q-03 · Operations and finance accounts | Seeded at start-up from environment variables; no admin UI |
| Q-05 · Authorisation expiry | The payment simulator keeps authorisations valid for 30 days; expiry is not handled in v1 |
| Q-07 · Where returns are received | Any active location; the receiving location is recorded per return |
| Q-08 · Size of simulated network | 2 warehouses and 8 stores in Polish cities, loaded as seed data |
| Q-09 · Forecast horizon and freshness | 14 days ahead, regenerated daily, stale after 48 hours |

## Architectural drivers

Eight PRD requirements decide the architecture; everything else is ordinary application design. Each driver is answered by a named mechanism later in this document.

| Driver (PRD) | What it demands | Architectural answer |
| --- | --- | --- |
| NFR-01, US-08 · No overselling | Atomic, concurrent-safe holds across locations | Conditional updates on stock rows in one transaction, fixed lock order (Stock reservation) |
| NFR-02, FR-ORD-02 · Idempotency | Repeated requests and messages act once | Idempotency keys on commands, inbox table on consumers |
| NFR-03 · Atomicity of state and event | No lost or orphan events | Transactional outbox in every service |
| NFR-04, BR-10 · Recovery | In-flight orders finish after any restart | Persistent, orchestrated saga in Orders with resumable steps |
| NFR-05 · Failure isolation | Checkout survives invoicing or forecasting outage | Billing and forecasting only consume events; nothing waits for them |
| NFR-06 · Bounded waiting | Slow provider does not block checkout | Timeouts, retries with backoff, circuit breakers; asynchronous checkout |
| NFR-14 · Replaceability | Swap strategy, provider, carrier, forecaster | Ports and adapters in every service; Strategy for allocation |
| Course grades 4.0–4.5 | Integration tests, patterns, independent services | Six services, HTTP and Kafka, tests against real PostgreSQL and Kafka |

Constraints C-01 (one developer) and C-03 (one machine, free tools) push the other way: the design avoids extra infrastructure that no driver needs, such as a separate search engine or a service mesh.

## Domain model

The domain splits into six bounded contexts, one per service; each aggregate below belongs to exactly one context and protects the listed invariants inside a single database transaction. Event Storming results will refine this section; names follow the PRD glossary, with "reservation" as the technical term for a hold.

### Bounded contexts

| Context | Responsibility | Upstream of | Relationship |
| --- | --- | --- | --- |
| Customers | Identity, roles, profiles, addresses | All contexts | Publishes a token format (open host service); others conform |
| Catalog | Products, variants, categories, prices, search | Orders, Inventory | Orders reads prices over HTTP; Inventory replicates variants from events |
| Inventory | Locations, stock, reservations, allocation, sales history, forecasts | Orders, Catalog | Orders calls it as a supplier; Catalog keeps an availability read model from its events |
| Orders | Carts, orders, shipments, returns, checkout saga | Billing | Orchestrates Inventory and Payments; Billing conforms to its shipment events |
| Payments | Authorisations, captures, voids, refunds | Orders | Anti-corruption layer around the payment provider |
| Billing | Invoices, receipts, correction invoices, numbering | — | Downstream only; never blocks other contexts |

### Aggregates and invariants

| Aggregate | Context | Invariants |
| --- | --- | --- |
| User | Customers | Email unique; exactly one role; at most one default address |
| Product (with Variants) | Catalog | (product, size, colour) unique; SKU unique; archived variants are not sellable |
| StockItem (variant × location) | Inventory | 0 ≤ reserved ≤ on hand; available = on hand − reserved − safety quantity ≥ 0 for new reservations |
| Reservation | Inventory | One per order; all lines held or none; status moves Held → Confirmed → Committed, or Held/Confirmed → Released, or Held → Expired |
| Order | Orders | Prices fixed at checkout; status follows the life cycle in the PRD; cancel only before first dispatch |
| Shipment | Orders | Belongs to one order and one location; Created → Dispatched → Delivered, or On hold |
| Return | Orders | Only delivered units, within 14 days; refunded quantity ≤ shipped quantity |
| Payment | Payments | captured ≤ authorised; refunded ≤ captured; each operation applied once per idempotency key |
| Invoice | Billing | Immutable once issued; number unique and gap-free per series; lines sum to totals |

## System architecture

The system runs as six independently deployable services behind one gateway, with a server-rendered web app in front; each service owns its database, commands and queries travel over HTTP, and facts travel as events over Kafka.

&#91;embedded content: container view · 6 services, gateway, web app, Kafka, simulators\]

Not drawn: Orders also calls Catalog, Inventory and Payments directly over internal HTTP during the checkout saga, and every container sends traces to Jaeger.

| Container | Responsibility | Owns data | Public API | Runs as |
| --- | --- | --- | --- | --- |
| Web app | Customer, operations and finance screens | Session cookie only | Pages on :8000 | Python process |
| API gateway | Single entry point; routes /api/v1/\* to services; hides /internal/\* | — | :8080 | nginx |
| Customers | Registration, login, tokens, profiles, addresses | customers\_db | /api/v1/auth, /customers | Service + outbox relay |
| Catalog | Products, variants, categories, prices, search, availability read model | catalog\_db | /api/v1/products, /categories | Service + relay + consumer |
| Inventory | Locations, stock, reservations, allocation, sales history, forecasts | inventory\_db | /api/v1/locations, /stock, /forecasts | Service + relay + consumer + expiry sweeper + forecast job |
| Orders | Cart, checkout, orders, shipments, returns, saga | orders\_db | /api/v1/cart, /orders, /returns | Service + relay + consumer + saga worker |
| Payments | Authorise, capture, void, refund through the provider | payments\_db | /api/v1/payments (read) | Service + relay |
| Billing | Invoices, receipts, correction invoices | billing\_db | /api/v1/invoices | Service + relay + consumer |
| Kafka | Domain event log | Topics | — | Single broker, KRaft mode |
| PostgreSQL | One logical database per service, one server locally | — | — | One container |
| Simulators | Payment provider, carrier, store sales feed | Their own state | Internal HTTP only | One Python process |
| Jaeger | Collects and shows traces | Traces | :16686 | All-in-one container |

One PostgreSQL server holding six databases keeps the laptop footprint small (C-03) while preserving database-per-service: each service has its own credentials and can reach only its own database.

## Minimal frontend

The frontend is a thin, server-rendered web app that calls the public API through the gateway exactly like any other client, so the API remains the product and the UI adds no business logic. It is written in Python to keep one language in the project (C-01).

**Technology.** FastAPI with Jinja2 templates, HTMX for partial page updates (cart, order status polling) and Pico.css for default styling. No build step, no JavaScript framework.

**Authentication.** The web app logs in through the Customers API and keeps the access token in an HttpOnly, SameSite=Lax session cookie; forms carry a CSRF token.

| ID | Screen | Role | Release |
| --- | --- | --- | --- |
| FR-WEB-01 | Register, log in, log out | All | R1 |
| FR-WEB-02 | Catalogue list with filters and search; product page with variant availability | Customer | R1 |
| FR-WEB-03 | Cart, checkout with address choice, order status page that polls until Confirmed or Rejected | Customer | R2 |
| FR-WEB-04 | Order history and details with shipments, tracking and documents; cancel button | Customer | R2 |
| FR-WEB-05 | Stock per variant and location; orders by status; record a return | Operations | R3 |
| FR-WEB-06 | Invoice and correction invoice list by period | Finance | R3 |

Out of scope for the web app: catalogue editing (done through the API and Swagger UI), responsive design beyond the CSS defaults, accessibility audits.

## Interfaces

Every service exposes a versioned REST API described contract-first in OpenAPI 3.1; public routes go through the gateway, internal routes are reachable only on the internal network. The OpenAPI files live in docs/api in the repository and are the source of truth; FastAPI implementations are tested against them (NFR-12).

### API conventions

| Topic | Convention |
| --- | --- |
| Versioning | Path prefix /api/v1 (public) and /internal/v1 (service to service) |
| Errors | RFC 9457 problem details (type, title, status, detail, instance) plus a code field, e.g. STOCK\_UNAVAILABLE |
| Idempotency | Idempotency-Key header (UUID) required on POST that creates or changes money or stock; replay returns the stored response |
| Pagination | page and size query parameters, response carries items, total, page, size; size ≤ 100 |
| Money | Decimal strings with two places ("129.99") and a currency field; never floats |
| Time | ISO 8601 in UTC |
| Tracing | W3C traceparent header accepted and propagated; X-Request-ID echoed |
| Async results | Long operations return 202 Accepted with a Location header to poll |

### Endpoint overview

| Service | Method and path | Purpose | Caller | PRD |
| --- | --- | --- | --- | --- |
| Customers | POST /api/v1/auth/register · POST /auth/login | Register; obtain access token | Anyone | FR-CUS-01, 02 |
| Customers | GET, PATCH /api/v1/customers/me | Profile | Customer | FR-CUS-03 |
| Customers | GET, POST, PUT, DELETE /api/v1/customers/me/addresses | Addresses, default flag | Customer | FR-CUS-04 |
| Customers | GET /.well-known/jwks.json | Public keys for token checks | Services | FR-CUS-05 |
| Catalog | GET /api/v1/products · GET /products/{id} | Browse, filter, search; product with variant availability | Anyone | FR-CAT-06–08 |
| Catalog | POST, PATCH /api/v1/products · POST /products/{id}/variants · POST /products/{id}/archive | Maintain catalogue | Operations | FR-CAT-01–03, 09 |
| Catalog | GET, POST /api/v1/categories | Categories | Anyone / Operations | FR-CAT-04, 05 |
| Catalog | POST /internal/v1/price-quotes | Current prices and VAT for a list of SKUs | Orders | FR-ORD-03 |
| Inventory | GET, POST, PATCH /api/v1/locations | Locations | Operations | FR-INV-01 |
| Inventory | GET /api/v1/stock · POST /stock/movements | Stock view; receipts and corrections | Operations | FR-INV-02–04 |
| Inventory | PUT /api/v1/settings/allocation-strategy | Choose strategy | Operations | FR-INV-11, FR-FCS-03 |
| Inventory | GET /api/v1/forecasts | Expected sales, stockout risk, forecast age | Operations | FR-FCS-05 |
| Inventory | POST /internal/v1/reservations · POST /reservations/{id}/confirm · /release | Allocate and hold; confirm; release | Orders | FR-INV-05–09 |
| Orders | GET, POST, PATCH, DELETE /api/v1/cart/lines | Cart | Customer | FR-ORD-01 |
| Orders | POST /api/v1/orders | Checkout (202, Idempotency-Key) | Customer | FR-ORD-02–04 |
| Orders | GET /api/v1/orders · GET /orders/{id} | History and details with shipments | Customer / Operations | FR-ORD-05, 07, 08, FR-SHP-04 |
| Orders | POST /api/v1/orders/{id}/cancel | Cancel | Customer | FR-ORD-06 |
| Orders | POST /api/v1/orders/{id}/returns · POST /returns/{id}/receipt | Request return; record received units | Customer / Operations | FR-ORD-09, FR-INV-14 |
| Orders | POST /internal/v1/carrier-events | Carrier webhooks (picked up, delivered) | Carrier simulator | FR-SHP-03 |
| Payments | POST /internal/v1/authorizations · /captures · /voids · /refunds | Payment operations | Orders | FR-PAY-01–04 |
| Payments | GET /api/v1/payments · GET /payments/{id} | Payment status and history | Customer / Finance | FR-PAY-05 |
| Billing | GET /api/v1/invoices · GET /invoices/{id} · GET /invoices/{id}/pdf | Documents; PDF (Could) | Customer / Finance | FR-BIL-05, 07 |

## Event catalogue

Services announce facts as versioned events on one topic per producing context, keyed by aggregate ID so that events of one order or stock item stay in order. The full schemas are kept in an AsyncAPI 3.0 file in docs/api; consumers must ignore unknown fields so producers can add fields without breaking them.

**Envelope.** Every event carries event\_id (UUID, used for de-duplication), event\_type, event\_version, occurred\_at, aggregate\_id, correlation\_id, causation\_id and payload. Trace context travels in Kafka headers.

| Topic | Event | Key | Consumers | Purpose |
| --- | --- | --- | --- | --- |
| catalog.events | VariantCreated, VariantArchived | variant\_id | Inventory | Keep the local list of sellable SKUs |
| inventory.events | StockAvailabilityChanged | variant\_id | Catalog | Update the online availability read model (FR-CAT-08) |
| inventory.events | ReservationExpired | order\_id | Orders | Reject an order whose hold expired (BR-04) |
| orders.events | OrderConfirmed, OrderRejected, OrderCancelled | order\_id | — (audit, future use) | Order history for other contexts |
| orders.events | ShipmentDispatched | order\_id | Inventory, Billing | Commit reserved units; issue the shipment invoice with lines, prices, VAT and capture reference (FR-INV-10, FR-BIL-01) |
| orders.events | ShipmentDelivered | order\_id | — | Delivery facts for tracking and analytics |
| orders.events | ReturnReceived | order\_id | Inventory | Restock sellable units, write off damaged ones (FR-INV-14) |
| orders.events | ReturnRefunded | order\_id | Billing | Issue the correction invoice (FR-BIL-04) |
| payments.events | PaymentAuthorized, PaymentCaptured, PaymentVoided, PaymentRefunded | payment\_id | — (finance audit) | Money movement log |
| billing.events | InvoiceIssued, CorrectionInvoiceIssued | order\_id | Orders | Link documents to the order view (FR-ORD-05) |
| store-sales.events | StoreSaleRecorded | location\_id | Inventory | Reduce store stock and grow sales history (FR-INV-13) |

Events that carry everything a consumer needs (event-carried state transfer) keep Billing and Catalog from calling back into Orders or Inventory, which is what lets them fail without blocking checkout (NFR-05).

## Checkout saga

Checkout is an orchestrated saga owned by Orders: the API accepts the order at once (202, status Pending) and a saga worker drives four steps, each idempotent and each with a compensation. The saga state is stored in orders\_db, so a restart resumes from the last completed step (NFR-04).

&#91;embedded content: checkout saga · happy path with compensations\]

Every failure on the right ends in Rejected with nothing held and nothing charged; the table gives each step's details.

| Step | Call | Success | Failure and compensation | PRD |
| --- | --- | --- | --- | --- |
| 0 · Accept | POST /api/v1/orders; prices from Catalog price-quotes | Order Pending, saga row created in the same transaction | Same Idempotency-Key → original order returned; invalid cart → 422, no order | FR-ORD-02, 03 |
| 1 · Reserve | Inventory POST /internal/v1/reservations | Reservation Held with allocation plan, expires in 15 min | Unavailable → order Rejected (STOCK\_UNAVAILABLE); nothing to compensate | FR-INV-05–07, BR-01, BR-06 |
| 2 · Authorise | Payments POST /internal/v1/authorizations | Authorised | Declined → release reservation → Rejected; timeout → query provider by idempotency key, then decide | FR-PAY-01, 06, BR-10 |
| 3 · Confirm hold | Inventory POST /reservations/{id}/confirm | Reservation Confirmed, no expiry | Already expired → void authorisation → Rejected (reservation expired) | BR-04, BR-05 |
| 4 · Complete | Local transaction in Orders | Shipments created from the plan; order Confirmed; OrderConfirmed in outbox; carrier booking queued | Local only; retried until it succeeds | FR-ORD-04, FR-SHP-01 |

**Worker mechanics.** The saga worker selects due rows with FOR UPDATE SKIP LOCKED, runs one step, and records the result with the next run time. Transient errors retry with exponential backoff (1 s, 2 s, 4 s); after the retry budget the saga compensates. Each step sends its own idempotency key (order\_id + step), so a step repeated after a crash has no double effect.

## Other key flows

Five more flows complete the order life cycle; each is driven by Orders and each leaves the system consistent if any single step fails.

### Dispatch and capture (FR-SHP-02, 03, FR-PAY-02, BR-09)

1. After confirmation, Orders books each shipment with the carrier adapter and stores the tracking number.
2. The carrier simulator later posts a picked-up event to /internal/v1/carrier-events.
3. Orders asks Payments to capture the shipment amount (plus the delivery fee on the first shipment) with key shipment\_id + "capture".
4. On success the shipment becomes Dispatched and ShipmentDispatched goes to the outbox; Inventory commits the units and Billing issues the invoice from that event.
5. If capture still fails after retries, the shipment becomes On hold and appears in the operations order list.

### Delivery (FR-SHP-03, BR-17)

1. The carrier simulator posts a delivered event; the shipment becomes Delivered.
2. Orders recomputes the order status from its shipments and publishes ShipmentDelivered.

### Cancellation (FR-ORD-06, BR-11)

1. Orders checks that no shipment is dispatched, then records a cancellation request in the same transaction (an internal saga state; the customer keeps seeing Confirmed until it completes).
2. The saga worker releases the reservation, voids the authorisation and cancels carrier bookings, then sets Cancelled and publishes OrderCancelled.

### Hold expiry (FR-INV-08, BR-04)

1. An Inventory sweeper runs every 30 s and releases Held reservations past expires\_at, then publishes ReservationExpired.
2. Orders consumes it; a saga still before step 3 rejects the order. A saga already at step 3 gets the same answer from the confirm call, so the two paths cannot disagree.

### Return and refund (FR-ORD-09, FR-PAY-04, FR-BIL-04, BR-14–16)

1. The customer requests a return of delivered units within 14 days; Orders creates a Return in status Requested.
2. Operations records the received units, their condition and the receiving location; Orders publishes ReturnReceived and Inventory restocks or writes off.
3. Orders asks Payments to refund the accepted amount (plus the delivery fee if the whole order is returned).
4. On success Orders publishes ReturnRefunded; Billing issues the correction invoice against each original shipment invoice.

## Stock reservation and allocation

Overselling is prevented by the database itself: a reservation succeeds only through conditional updates that check availability in the same statement, all inside one transaction. Allocation is a pure domain module, shared by the service and the simulator, that proposes a plan; the database then accepts or refuses it.

### Reservation algorithm (FR-INV-07, NFR-01)

1. Build an allocation plan from a fresh read of stock levels (no locks).
2. Open a transaction; sort plan lines by (location\_id, variant\_id) so concurrent transactions lock rows in the same order and cannot deadlock.
3. For each line run `UPDATE stock_items SET reserved = reserved + :qty WHERE location_id = :loc AND variant_id = :var AND on_hand - reserved - safety_qty >= :qty`.
4. If any update touches 0 rows, roll back, rebuild the plan from fresh data and retry, at most 3 times; then answer STOCK\_UNAVAILABLE.
5. Otherwise insert the reservation and its lines, write StockAvailabilityChanged to the outbox, and commit.

A CHECK constraint (0 ≤ reserved ≤ on\_hand) on stock\_items is the last line of defence. Committing a dispatched shipment lowers on\_hand and reserved by the same quantity in one statement.

### Allocation plan (FR-INV-05, 06, 11, BR-06, BR-07)

- **Eligibility (Specification pattern).** A location is eligible for a line if it is active, ships online orders and has available ≥ 1. Specifications combine with and/or, so new rules are added without touching strategies.
- **Candidate plans.** For each line, prefer locations that can ship the full quantity; split a line only when none can. Plans with more than 3 shipments are discarded.
- **Strategy (Strategy pattern).** A strategy scores every candidate plan; the lowest cost wins. Ties break by fewer shipments, then lower location ID, so results are deterministic.

| Strategy | Cost of a plan |
| --- | --- |
| Nearest | Sum of distances from shipping locations to the delivery address |
| Cheapest | Sum over shipments of (base cost + cost per km × distance) |
| Fewest parcels | Number of shipments, then cheapest as tie-break |
| Forecast-aware (R4) | Cheapest cost + parcel penalty × extra shipments + Σ lost-sale risk × margin of each unit taken from a store |

Distances use straight-line (haversine) distance between location coordinates and the address's city coordinates, looked up from a seed table of Polish cities; real routing is out of scope. With up to \~10 locations and a handful of lines, candidate plans are enumerated with pruning in well under 50 ms.

## Data

Each service owns one PostgreSQL database and is the only writer and reader of it; other services see its data only through its API or its events. Schema changes are versioned Alembic migrations that run at service start-up.

**Common rules.** Primary keys are UUIDs (v7, time-ordered). Money is NUMERIC(12,2) and VAT rates NUMERIC(5,4), mapped to Python Decimal (NFR-11). Timestamps are timestamptz in UTC. Every service has an outbox table and, if it consumes events, an inbox table (see Consistency and resilience). Rows that matter for audit are never updated in place: status changes and stock movements are appended to history tables (NFR-09).

| Service | Main tables | Key constraints |
| --- | --- | --- |
| Customers | users, profiles, addresses, signing\_keys | users.email unique; partial unique index on addresses(user\_id) where is\_default |
| Catalog | categories, products, variants, prices, variant\_availability (read model) | variants unique (product\_id, size, colour) and unique sku; tsvector index on products for search |
| Inventory | locations, sellable\_variants (replica), stock\_items, stock\_movements, reservations, reservation\_lines, store\_sales, demand\_forecasts, settings | stock\_items PK (location\_id, variant\_id), CHECK 0 ≤ reserved ≤ on\_hand; reservations.order\_id unique |
| Orders | carts, cart\_lines, orders, order\_lines, order\_status\_history, shipments, shipment\_lines, returns, return\_lines, saga\_instances, idempotency\_records | orders unique (customer\_id, idempotency\_key); saga\_instances PK order\_id |
| Payments | payments, payment\_operations | payment\_operations.idempotency\_key unique; CHECK captured ≤ authorised, refunded ≤ captured |
| Billing | invoices, invoice\_lines, number\_sequences, receipts | invoices.number unique; one invoice per (shipment\_id, type = invoice) |

**Gap-free numbering (FR-BIL-03, BR-13).** Billing locks the row for (series, month) in number\_sequences with SELECT … FOR UPDATE, increments it and inserts the invoice in the same transaction; a rolled-back transaction therefore never burns a number.

**Snapshots.** Orders stores the price, VAT rate, product name, size and colour on each order line and the full delivery address on the order, so later catalogue or profile changes never alter history (BR-02).

ER diagrams per service are produced in the TRD appendix once Event Storming confirms the aggregates.

## Consistency and resilience

The system is eventually consistent between services and strictly consistent inside each one; five mechanisms, all in a shared library, make that safe.

| Mechanism | How it works | PRD |
| --- | --- | --- |
| Transactional outbox | A state change and its event are written in the same database transaction; a relay process reads unsent rows with FOR UPDATE SKIP LOCKED, publishes them to Kafka, marks them sent. Delivery is at least once. | NFR-03 |
| Idempotent consumer (inbox) | Each consumer inserts event\_id into its inbox table in the same transaction as its own change; a duplicate insert means the event was already handled and is skipped. Offsets are committed after the transaction. | NFR-02 |
| Idempotent commands | POST requests that move money or stock carry an Idempotency-Key; the first response is stored with the key and replayed for repeats. Payment operations are unique per key in payments\_db and are passed to the provider. | NFR-02, FR-ORD-02, BR-10 |
| Timeouts and retries | Internal HTTP: 2 s timeout, up to 3 retries with exponential backoff and jitter, only for idempotent calls. Provider calls: 3 s timeout. Checkout as a whole answers within 10 s because the API returns 202 at once. | NFR-06 |
| Circuit breaker | Per downstream dependency: opens after 5 consecutive failures, rejects calls for 30 s, then lets one trial call through. An open breaker fails a saga step fast, so the worker reschedules instead of waiting. | NFR-06 |

**Failure behaviour by component.**

| Component down | What still works | What happens on recovery |
| --- | --- | --- |
| Billing | Checkout, dispatch, delivery | Billing reads the backlog of ShipmentDispatched and ReturnRefunded events and issues the missing documents |
| Payments or provider | Browsing, cart; new orders wait in Pending | Saga resumes; holds that expired meanwhile lead to Rejected (BR-04) |
| Inventory | Browsing (availability may be stale) | Saga step 1 resumes; expiry sweeper releases stale holds |
| Kafka | All synchronous APIs; events pile up in outboxes | Relays drain outboxes in order per aggregate |
| Orders | Browsing, stock management | Saga worker resumes every non-final saga from its stored step |

## Security

Customers is the only token issuer; every other service checks tokens itself with the issuer's public key, so a compromised gateway cannot mint access. The threat model below is a short STRIDE pass for a local, course-scale system (NFR-10).

- **Passwords.** Hashed with Argon2id; minimum length 10; login errors do not reveal which field was wrong (US-01).
- **Tokens.** JWT signed with RS256, 15-minute lifetime, claims sub, role, exp, iat, jti. Keys are published at /.well-known/jwks.json and cached by services for 10 minutes. Refresh tokens are a Could (FR-CUS-06).
- **Authorisation.** A shared dependency checks the role per endpoint; ownership checks (customer\_id = sub) live in the application layer of each service, not in the gateway (FR-CUS-05).
- **Internal routes.** /internal/\* is not routed by the gateway and listens only on the Docker internal network. In v1 the internal network is trusted; service-to-service tokens are listed as TQ-03.
- **Payment data.** No card data enters the system; the simulator returns opaque references (FR-PAY-07).
- **Secrets.** Read from environment variables; a committed .env.example holds dummy values; real .env is git-ignored and checked by a pre-commit secret scan.
- **Input.** All request bodies are validated by Pydantic models with size limits; SQL goes only through parameterised queries.

| STRIDE threat | Example | Control |
| --- | --- | --- |
| Spoofing | Forged token | RS256 signature check, short expiry |
| Tampering | Changed price in checkout request | Prices always taken from Catalog, never from the client |
| Repudiation | Disputed refund | Append-only payment\_operations and order\_status\_history with actor |
| Information disclosure | Reading another customer's order | Ownership check on every customer endpoint; tested in US-02 |
| Denial of service | Checkout flood holding all stock | Holds expire in 15 minutes; per-customer rate limit at the gateway |
| Elevation of privilege | Customer calling an operations endpoint | Role check per endpoint; tested in US-03 |

## Observability

One trace follows a customer request through every HTTP call, Kafka event and saga step it causes, which satisfies NFR-08 and is the main debugging tool for a distributed flow.

- **Tracing.** OpenTelemetry SDK with automatic instrumentation for FastAPI, httpx and SQLAlchemy; trace context is written into Kafka message headers by the outbox relay and restored by consumers. Traces go to Jaeger over OTLP.
- **Correlation.** The trace ID is the correlation identifier. It is copied into every event envelope (correlation\_id) and saga row, and returned to clients as X-Request-ID.
- **Logs.** Structured JSON to stdout with timestamp, level, service, trace\_id, span\_id and event fields; no personal data beyond IDs.
- **Health.** /health/live (process up) and /health/ready (database and Kafka reachable) on every service, used by Docker Compose health checks.
- **Audit.** Status and stock history tables (see Data) answer who changed what and when (NFR-09).
- **Metrics.** Optional in v1 (Prometheus endpoint per service); the forecasting simulator produces its own result metrics.

## Service internals and design patterns

Every service has the same hexagonal layout, so business rules never import a framework, a database driver or a Kafka client; that is what makes NFR-13 (rules testable without I/O) and NFR-14 (replaceable adapters) hold.

| Layer | Contains | May depend on |
| --- | --- | --- |
| domain | Entities, value objects (Money, Sku, Quantity), aggregates, domain events, policies, strategies, specifications | Nothing outside the standard library |
| application | Use cases (one class per command or query), ports (abstract repositories, gateways, publishers), unit of work | domain |
| adapters/inbound | FastAPI routers, Kafka consumers, saga worker, schedulers | application |
| adapters/outbound | SQLAlchemy repositories, outbox writer, httpx clients, provider and carrier adapters, forecaster | application ports |
| bootstrap | Dependency wiring, settings, app factory | All layers |

An import-linter contract in CI fails the build if a lower layer imports a higher one.

| Pattern | Where | Problem it solves | PRD |
| --- | --- | --- | --- |
| Ports and adapters | All services | Business rules independent of I/O | NFR-13, NFR-14 |
| Strategy | Inventory allocation strategies | Switch allocation rule at run time | FR-INV-11, FR-FCS-03 |
| Specification | Inventory location eligibility | Composable eligibility rules | FR-INV-06, BR-07 |
| State | Order, Shipment, Reservation, Return | Only legal status transitions | Order life cycle, BR-17 |
| Saga (orchestration) | Orders checkout, cancellation, returns | Consistency across services without distributed transactions | FR-ORD-04, NFR-04 |
| Transactional outbox | All services | State and event never diverge | NFR-03 |
| Idempotent consumer | All consumers | Duplicate events have no effect | NFR-02 |
| Adapter / anti-corruption layer | Payments provider, carrier, forecaster | Keep external models out of the domain | NFR-14 |
| Circuit breaker, Retry | All outbound HTTP clients | Bounded waiting under failure | NFR-06 |
| Repository, Unit of Work | All services | Persistence behind ports, one transaction per use case | NFR-13 |
| CQRS read model | Catalog variant availability | Fast availability without querying Inventory | FR-CAT-08 |

## Demand forecasting design

Forecasting is a module of the Inventory context with two parts: an offline pipeline that trains a versioned model, and a daily job that writes forecasts into inventory\_db; order processing only ever reads a table, so it never waits for a model (FR-FCS-01–05, NFR-05).

### Offline pipeline (forecasting/ package)

1. **Prepare data.** Load the chosen public dataset, map articles to variants and sales to the simulated locations. Missing dimensions (sizes, store split) are derived with documented, seeded rules (A-05, Q-10).
2. **Build features.** Sales lags (7, 14, 28 days), rolling means and standard deviations, day of week, month, price, category, size, location type.
3. **Train.** One global LightGBM model with a Poisson objective over all variant × location series.
4. **Validate.** Rolling-origin backtest on the last 8 weeks; WAPE and MAE against two baselines: same day last week and 28-day moving average.
5. **Register.** Save the model file with metadata (version, training window, features, metrics) under models/\<version>/.

### Daily forecast job

A scheduled process in the Inventory deployment loads the current model, predicts the next 14 days for every sellable variant and location, and replaces demand\_forecasts rows with model\_version and generated\_at. Stockout risk is derived when read, from current available stock and expected demand.

### Use in allocation

For a unit taken from store s with available quantity a, expected demand D over the next L days (L = replenishment time, default 7) is treated as Poisson with mean equal to the summed forecast. The extra lost-sale cost of taking that unit is the probability that demand reaches a, times the unit margin:

```latex
\text{cost}_{\text{lost}}(s, v) = P\left(D_{s,v} \ge a_{s,v}\right) \times \text{margin}_v, \quad D_{s,v} \sim \text{Poisson}\Big(\sum_{d=1}^{L} \hat{y}_{s,v,d}\Big)
```

If a forecast is missing or older than 48 hours, ŷ is replaced by the 28-day moving average of recorded sales for that variant and location (FR-FCS-04).

### Simulator

The simulator replays held-out demand day by day over the simulated network: store walk-in demand, online orders, replenishment every L days. It imports the same allocation package as the Inventory service, so it measures the real code. Each strategy runs 30 times with different seeds; results report fill rate, lost sales, cost per order, parcels per order and promise compliance, with 95% confidence intervals. An oracle strategy uses actual future demand as an upper bound.

## Testing strategy

Tests follow a pyramid: many fast unit tests on pure domain code, fewer integration tests against real PostgreSQL and Kafka, and a small set of end-to-end scenarios that replay the PRD user stories. Every Must requirement has at least one automated test (NFR-13).

| Level | Scope | Tools | Runs |
| --- | --- | --- | --- |
| Unit | Domain and application layers: state machines, allocation strategies, specifications, VAT and rounding, reservation rules, saga step decisions, forecast fallback | pytest, Hypothesis for property-based tests (e.g. reserved never exceeds on hand; invoice lines always sum to totals) | Every commit, < 30 s per service |
| Integration | One service with its real database and Kafka: repositories, migrations, outbox relay, inbox de-duplication, conditional reservation updates | pytest, Testcontainers (PostgreSQL, Kafka) | Every push |
| Contract | Each service's HTTP API against its OpenAPI file; event payloads against the AsyncAPI schemas | Schemathesis, JSON Schema validation | Every push |
| End-to-end | The whole system in Docker Compose: US-01 to US-14 as scenarios | pytest + httpx against the gateway | Before each release gate |
| Concurrency | 20 simultaneous checkouts for 1 unit (US-08) | asyncio + httpx | Before R2 gate |
| Failure | Provider timeouts and declines, killed services, Kafka outage (NFR-03–06) | Simulator failure modes, Toxiproxy, docker compose stop | Before R2 and R3 gates |
| Performance | NFR-07 targets with 10,000 variants | Locust | Before R3 gate |

**Traceability.** Tests are tagged with the requirement they verify, for example `@pytest.mark.req("FR-ORD-02", "US-07")`. A CI step builds a matrix of requirement → tests → result and fails if a Must requirement in the current release has no passing test.

**Coverage targets.** At least 90% line coverage for domain packages and 75% overall, measured with coverage.py; coverage is a guide, the traceability matrix is the gate.

## Technology stack

The whole stack is free and open source and stays in one language, Python, except for infrastructure containers (C-03). Library choices marked TQ are still open.

| Concern | Choice | Why |
| --- | --- | --- |
| Language | Python 3.13 | Course requirement; one language for services, frontend and ML |
| Web framework | FastAPI, Pydantic v2, Uvicorn | Async, OpenAPI out of the box, typed validation |
| Database | PostgreSQL 17 | Transactions, conditional updates, SKIP LOCKED, full-text search |
| Data access | SQLAlchemy 2.0 (async) with asyncpg; Alembic migrations | Mature ORM and Core for explicit SQL where it matters (reservations) |
| Messaging | Apache Kafka in KRaft mode; aiokafka client (TQ-01) | Ordered, durable event log; no ZooKeeper |
| HTTP client | httpx | Async, timeouts, test transport |
| Resilience | tenacity for retries; circuit breaker in the shared library | Small, explicit, testable |
| Security | PyJWT (RS256), argon2-cffi | Standard token and password handling |
| Frontend | Jinja2, HTMX, Pico.css | No build step, Python only |
| Gateway | nginx | Simple static routing and rate limiting |
| Observability | OpenTelemetry SDK, Jaeger all-in-one | Vendor-neutral tracing across HTTP and Kafka |
| Forecasting | pandas, scikit-learn, LightGBM, SciPy | Feature work, baselines, gradient boosting, Poisson probabilities |
| Testing | pytest, pytest-asyncio, Hypothesis, Testcontainers, Schemathesis, Toxiproxy, Locust | Covers every level of the test strategy |
| Code quality | uv, ruff, mypy (strict on domain), import-linter, pre-commit, gitleaks | Fast installs, lint, types, layer rules, secret scanning |
| Runtime | Docker, Docker Compose | One-command start (NFR-15) |
| CI | GitHub Actions | Free for public repositories; runs Testcontainers |
| API specifications | OpenAPI 3.1, AsyncAPI 3.0 | Contract-first HTTP and event interfaces (NFR-12) |

## Repository, local environment and CI

The code and the project documents live in one Git repository (monorepo), clothes-order-management-system, managed as a uv workspace; PRD, TRD, ADRs and API specifications are in its docs/ folder. Only the Obsidian knowledge base and CLAUDE.md sit beside it in the COMS workspace folder and are never committed.

```
COMS/                                   workspace folder, not under version control
├── CLAUDE.md                           instructions for Claude Code
├── knowledge-base/                     Obsidian vault: plan, session logs, notes
└── clothes-order-management-system/    Git repository, pushed to GitHub
    ├── README.md             overview, architecture summary, setup and test instructions
    ├── docs/                 prd.md, trd.md, adr/, api/openapi/*.yaml, api/asyncapi.yaml
    ├── services/
    │   ├── customers/        src/customers/{domain,application,adapters,bootstrap}, tests/{unit,integration}, migrations/, Dockerfile
    │   ├── catalog/
    │   ├── inventory/        + allocation/ (pure package, also used by the simulator), forecast job
    │   ├── orders/           + saga worker
    │   ├── payments/
    │   └── billing/
    ├── libs/platform/        outbox, inbox, Kafka, idempotency, auth, errors, tracing, circuit breaker
    ├── web/                  minimal frontend
    ├── simulators/           payment provider, carrier, store sales feed
    ├── forecasting/          data preparation, training, evaluation, allocation simulator
    ├── deploy/               docker-compose.yml, nginx.conf, seed data
    ├── tests/e2e/            user-story scenarios against the running system
    └── pyproject.toml        uv workspace root
```

**Local environment.** `docker compose up` starts PostgreSQL, Kafka, Jaeger, nginx, the six services, the web app and the simulators, then loads seed data (categories, products, 2 warehouses, 8 stores, stock, seeded operations and finance users). Target footprint: under 6 GB RAM, measured in R0 (TR-04).

**Configuration.** Twelve-factor style: all settings through environment variables, documented in .env.example; strategy, hold time limit, retry budgets and simulator failure rates are configurable.

**Git workflow.** Trunk-based: short-lived branches, pull requests into main, Conventional Commits, semantic version tags per release (v0.1.0 = R1). Only the developer commits and pushes; Claude Code proposes commit messages but never runs commit or push.

**CI pipeline (GitHub Actions).** On every push: ruff, mypy, import-linter, unit tests, gitleaks. On pull requests also: integration and contract tests per changed service, Docker image builds. Before a release tag: end-to-end, concurrency and failure suites, and the traceability matrix.

## Implementation plan

Work follows the PRD releases; inside each release the order below puts shared foundations first and builds every feature as a vertical slice (API, domain, persistence, events, tests, screen).

### R0 · Foundations

1. Event Storming; update the Domain model section and write ADR-001 to ADR-013.
2. uv workspace, service template with hexagonal layout, import-linter contract.
3. libs/platform: settings, errors, auth dependency, tracing, outbox writer and relay, inbox, idempotency store.
4. Docker Compose with PostgreSQL, Kafka, Jaeger, nginx; health checks; CI pipeline.
5. OpenAPI skeletons per service and the AsyncAPI file with the event envelope.

### R1 · Accounts and catalogue

1. Customers: registration, login, JWKS, profile, addresses, seeded staff accounts.
2. Catalog: categories, products, variants, prices, browse and search; VariantCreated events.
3. Inventory: locations, stock items, stock movements, sellable variant replica; StockAvailabilityChanged; Catalog availability read model.
4. Web: login, catalogue, product page.

### R2 · Order to cash (MVP)

1. Allocation package (Specification, Strategy: nearest, cheapest, fewest parcels) with property-based tests.
2. Inventory reservations: create, confirm, release, commit, expiry sweeper; concurrency test.
3. Simulators: payment provider and carrier with failure modes.
4. Payments: authorise, capture, void, refund with idempotent operations, provider adapter, circuit breaker.
5. Orders: cart, checkout API, saga worker steps 1–4 with compensations; shipments; carrier webhooks; dispatch and capture; cancellation.
6. Billing: invoice from ShipmentDispatched, VAT, gap-free numbering, InvoiceIssued.
7. Web: cart, checkout, order status polling, order history, cancel.
8. Gate: US-06 to US-12 end to end, failure tests for NFR-01 to NFR-04.

### R3 · After-sales and hardening

1. Returns, receipt of returned units, refunds, correction invoices, receipts.
2. Store sales feed and safety quantities; strategy setting endpoint.
3. Order timeline, operations order list, estimated delivery dates, nested categories.
4. Web: operations and finance screens.
5. Failure, performance and security checks; finish OpenAPI, AsyncAPI, ADRs, C4 diagrams, setup and test guide.

### R4 · Demand forecasting

1. Dataset choice and mapping (Q-10); baselines and backtest.
2. LightGBM model, registry folder, daily forecast job, demand\_forecasts table, fallback.
3. Forecast-aware strategy and forecasts endpoint.
4. Simulator runs, 30 seeds per strategy, results report.

## Decision log

Thirteen decisions in this TRD are significant enough to record as architecture decision records (MADR format) in docs/adr during R0; each will list context, options and consequences in full.

| ADR | Decision | Main alternative rejected | Reason |
| --- | --- | --- | --- |
| ADR-001 | Six microservices, database per service (one PostgreSQL server locally) | Modular monolith | Course grade 4.5; failure isolation (NFR-05) |
| ADR-002 | HTTP for commands and queries, Kafka for domain events | Kafka for everything | Simpler request/response for saga steps; events where coupling must be loose |
| ADR-003 | Orchestrated saga in Orders | Choreography | One place to read and test the checkout flow; easier compensation |
| ADR-004 | Asynchronous checkout (202 + polling) | Synchronous checkout | Bounded response time under provider failures (NFR-06) |
| ADR-005 | Transactional outbox and inbox in every service | Dual writes; CDC with Debezium | Correctness without extra infrastructure |
| ADR-006 | Reservations via conditional updates with fixed lock order | Optimistic version columns; distributed lock | Single statement guarantees NFR-01; no extra component |
| ADR-007 | Shipments managed inside Orders | Separate Shipping service | Keeps service count at six; shipments share the order's life cycle |
| ADR-008 | Tokens issued by Customers (RS256), checked in each service | Validation only at the gateway | Defence in depth; gateway stays simple |
| ADR-009 | Monorepo with uv workspace and shared platform library | Repository per service | One developer; shared outbox and auth code |
| ADR-010 | Minimal frontend server-rendered with FastAPI, Jinja2, HTMX | React single-page app | One language, no build step, small scope |
| ADR-011 | PostgreSQL full-text search for the catalogue | Elasticsearch or OpenSearch | Catalogue size is small; fewer containers (C-03) |
| ADR-012 | Forecasting as an Inventory module with offline training and a daily job | Separate forecasting service with online inference | Order processing never waits for a model (NFR-05) |
| ADR-013 | OpenTelemetry with Jaeger for tracing | Logs only | End-to-end traceability across HTTP and Kafka (NFR-08) |

## Technical risks

The riskiest technical work is the saga with its failure paths; it is built and failure-tested first within R2, before the screens and Billing.

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| TR-01 | Saga edge cases (late provider answers, expiry races) cause stuck or inconsistent orders | High | High | Explicit state table per step; failure tests from the start of R2; a reconciliation job that lists sagas idle for more than 15 minutes |
| TR-02 | Outbox relay and inbox code has subtle bugs shared by all services | Medium | High | One shared implementation with its own integration tests; duplicate-delivery tests in every consumer |
| TR-03 | Deadlocks or contention on hot stock rows during concurrency tests | Medium | Medium | Fixed lock order; short transactions; retry on serialization errors |
| TR-04 | Kafka plus six services and PostgreSQL exceed laptop memory | Medium | Medium | JVM heap limit for Kafka; measure in R0; fall back to Redpanda if needed (TQ-02) |
| TR-05 | Async SQLAlchemy and aiokafka add complexity a solo developer struggles to debug | Medium | Medium | Tracing from R0; small, well-tested platform library; keep domain code synchronous and pure |
| TR-06 | Synthetic size and store splits make forecasts look better or worse than reality | High | Low | Document the rules, test sensitivity with two split settings, state limits in results |

## Open technical questions

Six technical questions remain open (TQ-07 is resolved); none blocks R0, and each should be closed with an ADR before the release that needs it.

- [ ] TQ-01 · Kafka client: aiokafka (pure Python, async) or confluent-kafka (librdkafka, faster, sync API)? Needed by R1.
- [ ] TQ-02 · Kafka or Redpanda as the local broker, if memory use in R0 is too high? Needed by R0.
- [ ] TQ-03 · Should service-to-service calls carry their own tokens, or is the internal network trusted for the course scope? Needed by R2.
- [ ] TQ-04 · Saga worker as a separate process or a background task inside the Orders API process? Needed by R2.
- [ ] TQ-05 · Invoice PDF generation library, if FR-BIL-07 is taken (WeasyPrint or ReportLab)? Needed by R3.
- [ ] TQ-06 · How to version the forecasting model: plain folders with metadata, or a local MLflow tracking server? Needed by R4.

* [x] TQ-07 · Resolved in TRD v0.3: docs/ (PRD, TRD, ADRs, API specifications) lives in the repository, so CI runs contract tests and reviewers see the full documentation; only the knowledge base and CLAUDE.md stay outside.
