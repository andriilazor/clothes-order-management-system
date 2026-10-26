# PRD - Clothes Order Management System

Oct 26, 2026 · @Andriy

## Document control

This PRD is the product baseline for development: it says what the system must do and why, never how. The TRD will describe how each requirement is built, and every TRD element, test and backlog item will reference an ID from this document.

| Field | Value |
| --- | --- |
| Product | clothes-order-management-system |
| Document | Product Requirements Document (PRD) |
| Version | 0.2 (draft) |
| Companion documents | TRD (planned), architecture decision records (planned) |
| Requirement IDs | FR-\<domain>-NN functional, NFR-NN non-functional, BR-NN business rules, US-NN user stories, A-NN assumptions, C-NN constraints, RSK-NN risks, R0–R4 releases, Q-NN open questions |
| Priorities | MoSCoW: Must, Should, Could, Won't (this time) |

Any change of scope after version 1.0 creates a new version and a row in the change history.

| Version | Date | Change |
| --- | --- | --- |
| 0.2 | 2026-10-26 | Minimal web frontend added: Overview, Non-goals, new domain WEB (FR-WEB-01–06), C-04 reworded, release scope updated |
| 0.1 | 2026-10-26 | First draft based on the project README |

## Overview

The product is an e-commerce backend (with minimum required frontend) that lets a fashion retailer sell online and ship each order from its central warehouses and physical stores without ever selling the same item twice.

It covers the standard e-commerce domains and adds the part most shops handle poorly: knowing where each item physically is, holding it safely while the customer pays, and choosing the best location to ship from.

Key capabilities:

- Customer accounts, login and delivery addresses.
- A catalogue of products with size and colour variants, prices and search.
- Stock per variant and location, with time-limited reservations.
- Checkout that is safe to retry and never oversells.
- An allocation decision that picks the shipping location(s) for every order line.
- Payment authorisation, capture per shipment and refunds through an external provider.
- Split shipments with tracking through an external carrier.
- Invoices per shipment with VAT, and correction invoices after returns.
- An extension that forecasts demand per variant and location, so allocation avoids taking the last unit from a store that is about to sell it.

## Problem statement

A fashion retailer that ships online orders from many locations loses sales and money in five recurring ways.

| # | Problem | Consequence | What the product must do |
| --- | --- | --- | --- |
| P1 | Each product has many variants (size × colour); a popular size sells out in minutes while other locations still hold it | Customers see "out of stock" although the item exists elsewhere | Track stock per variant and per location and sell from any eligible location |
| P2 | Concurrent orders compete for the same last unit | The same item is sold twice; one order must be cancelled | Reserve stock atomically before payment; never let reservations exceed physical stock |
| P3 | One basket can be available only across several locations | The retailer must choose between one slow parcel and several faster, more expensive ones | Build an allocation plan that weighs shipping cost, number of parcels and delivery promise |
| P4 | The nearest or cheapest location is not always the best | Shipping the last unit of a size from a store that would sell it in person costs a sale there | Take expected local demand into account when choosing a location |
| P5 | A payment provider or an internal component can fail mid-order | Money is taken without stock, or stock stays blocked without payment | Keep stock, payment and documents consistent after any single failure |

## Goals and success metrics

The product succeeds when it never oversells, never charges incorrectly and always reaches a consistent state, and when the forecasting hypothesis has been tested with a clear answer. Targets are verified in automated tests or in the allocation simulator, since there is no production traffic.

| Goal | Success metric | Target | Verified by |
| --- | --- | --- | --- |
| G1 · No overselling | Units sold beyond physical stock | 0 under concurrent checkouts for the same last unit | Concurrency test |
| G2 · Reliable checkout | Duplicate orders from a repeated checkout request | 0 | Automated test |
| G2 · Reliable checkout | Orders left in an intermediate state longer than the reservation time limit | 0, including after a component restart | Failure test |
| G3 · Correct money | Captured amounts without exactly one invoice | 0 | Reconciliation test |
| G3 · Correct money | Difference between invoice totals and captured amounts | 0.00 per document | Reconciliation test |
| G3 · Correct money | Refunds without a correction invoice | 0 | Reconciliation test |
| G4 · Smart fulfilment | Orders that could be fulfilled from available stock but were rejected | 0 | Simulator |
| G4 · Smart fulfilment | Parcels per order and fulfilment cost per order | Reported per allocation strategy | Simulator |
| G5 · Forecast value (extension) | Lost sales and cost per order, forecast-aware vs best rule-based strategy | Difference reported with 95% confidence interval; the hypothesis may be rejected | Simulator, repeated runs |
| G6 · Course | Grade components delivered | All components up to grade 5.0 | Course requirements mapping |

## Non-goals and out of scope

The following are deliberately not built, to keep a one-person project deliverable. Each can be revisited in a later PRD version.

- Native mobile apps, a designed storefront and catalogue editing screens. The web frontend covers only the screens in FR-WEB.
- Real payment providers and real carriers. Both are simulated with realistic behaviour, including failures.
- Integration with real store tills. In-store sales arrive as a simulated sales feed.
- Warehouse operations: picking, packing, labels, put-away.
- Promotions, discount codes, gift cards, loyalty programmes.
- Multiple currencies, multiple tax jurisdictions and international delivery.
- Business customers with company invoices (B2B).
- Backorders and pre-orders: an order is accepted only for stock that exists now.
- Recommendations, reviews, wish lists.
- Email or SMS notifications, password reset by email.
- Production hosting, scaling and high availability beyond what runs on one developer machine.

## Target users and personas

Three human roles use the system; each sees only what its role needs. Three external systems interact with it automatically.

| Role | Goal | Main tasks | Access |
| --- | --- | --- | --- |
| Customer | Buy clothes online and get them quickly | Register, browse and search, manage cart and addresses, place and track orders, cancel, return | Own profile, addresses, cart, orders, payments, invoices |
| Operations | Keep the catalogue and stock right and fulfil orders well | Maintain products, variants, prices and locations; adjust stock; follow orders and shipments; record returns; watch forecasts and stockout risk | Catalogue, locations, stock, all orders and shipments, forecasts |
| Finance | Have a correct document for every money movement | Review payments, invoices and correction invoices; reconcile captured amounts | Payments, invoices, correction invoices (read) |

| External system | Role in the product |
| --- | --- |
| Payment provider (simulated) | Authorises, captures, voids and refunds amounts; can decline, time out or be unavailable |
| Carrier (simulated) | Accepts shipments, returns a tracking number, reports dispatch and delivery |
| Store sales feed (simulated) | Reports in-store sales, which reduce store stock and feed demand forecasting |

## User journeys

Six journeys cover the full life of an order; J1 is the core of the MVP. Steps describe what the user experiences, not how the system implements it.

### J1 · Customer places an order

1. The customer browses or searches the catalogue and sees which sizes and colours are available.
2. The customer adds variants to the cart and chooses a saved delivery address.
3. The customer submits checkout. A repeated submission (for example after a network error) returns the same order.
4. The system holds the items in one or more locations and asks the payment provider to authorise the total.
5. The customer sees the order as confirmed, or as rejected with a reason (item no longer available, payment declined). A rejected order frees its items at once.

### J2 · Customer tracks an order

1. The customer opens the order history and selects an order.
2. The customer sees the order status, its shipments (one per shipping location), each shipment's tracking number and status, and the invoices issued so far.

### J3 · Customer cancels an order

1. Before the first shipment leaves, the customer cancels the order.
2. The held items return to stock, the payment authorisation is released, and the order shows as cancelled.

### J4 · Customer returns items

1. Within the return window after delivery, the customer requests a return of selected items.
2. Operations records the received items and their condition.
3. The customer is refunded for the accepted items; finance gets a correction invoice; sellable items go back to stock.

### J5 · Operations manages stock and fulfilment

1. Operations maintains products, variants, prices and locations, and records stock receipts and corrections.
2. Operations sees stock per variant and location, including held quantities, and follows orders and shipments by status.
3. With the extension, operations sees expected demand and stockout risk per variant and location.

### J6 · Finance reconciles documents

1. Finance lists invoices and correction invoices for a period.
2. Finance checks that every captured or refunded amount has exactly one matching document.

## Functional requirements

The product has 71 functional requirements in nine domains; the 47 Must requirements outside the forecasting extension form the MVP. Priorities follow MoSCoW; forecasting requirements are prioritised within the extension release.

### Customers (CUS)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-CUS-01 | A visitor can register with email and password; an email can be registered only once | Must |
| FR-CUS-02 | A registered user can log in and receives an access token that expires | Must |
| FR-CUS-03 | A customer can view and edit their profile (name, phone) | Must |
| FR-CUS-04 | A customer can add, edit and delete delivery addresses and mark one as default | Must |
| FR-CUS-05 | Every action is allowed only for the roles that need it (customer, operations, finance); a customer can access only their own data | Must |
| FR-CUS-06 | A user can refresh an expiring token without logging in again | Could |
| FR-CUS-07 | A user can reset a forgotten password by email | Won't |

### Catalogue (CAT)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-CAT-01 | Operations can create, update and archive products (name, description, brand, category, material) | Must |
| FR-CAT-02 | Each product has variants defined by size and colour; each variant has a unique SKU | Must |
| FR-CAT-03 | Each variant has a gross price and a VAT rate | Must |
| FR-CAT-04 | Operations can manage categories; products belong to one category | Must |
| FR-CAT-05 | Categories can be nested (for example Women › Dresses) | Should |
| FR-CAT-06 | Anyone can browse products with paging and filter by category, size, colour and price range | Must |
| FR-CAT-07 | Anyone can search products by text in name and description | Should |
| FR-CAT-08 | A product page shows, per variant, whether it is available online (in stock, low, out of stock), without revealing quantities per location | Should |
| FR-CAT-09 | Archived products and variants cannot be bought but stay visible in existing orders | Must |
| FR-CAT-10 | Price changes keep a history with the date each price became valid | Could |

### Stock and locations (INV)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-INV-01 | Operations can manage locations: type (warehouse or store), address and position, active flag, and whether it ships online orders | Must |
| FR-INV-02 | The system keeps on-hand quantity per variant and location | Must |
| FR-INV-03 | Operations can record stock receipts and corrections with a reason; every stock change is kept in a history | Must |
| FR-INV-04 | Operations can see per variant and location: on hand, held for orders, and available to sell | Must |
| FR-INV-05 | For each order the system builds an allocation plan that says which location ships each unit | Must |
| FR-INV-06 | Only eligible locations take part in allocation (active, ships online orders, enough available stock) | Must |
| FR-INV-07 | The system holds stock for a whole allocation plan in one step: either every unit is held or none is | Must |
| FR-INV-08 | A hold expires after a time limit and its units become available again | Must |
| FR-INV-09 | A hold is released at once when the order is rejected or cancelled | Must |
| FR-INV-10 | When a shipment is dispatched, its held units leave stock | Must |
| FR-INV-11 | Operations can choose the allocation strategy in use: nearest location, cheapest shipping, fewest parcels | Should |
| FR-INV-12 | Stores can keep a safety quantity per variant that is not offered online | Should |
| FR-INV-13 | In-store sales from the store sales feed reduce store stock and are kept as sales history | Should |
| FR-INV-14 | Returned units in sellable condition go back to stock at the receiving location; others are written off with a reason | Should |

### Orders and cart (ORD)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-ORD-01 | A customer can add variants to a cart, change quantities, remove lines and see the cart with current prices and total | Must |
| FR-ORD-02 | A customer can place an order from the cart with a delivery address; each checkout carries a client-chosen key, and a repeated request with the same key returns the original order | Must |
| FR-ORD-03 | An order keeps the prices, VAT rates and delivery fee valid at checkout | Must |
| FR-ORD-04 | After checkout the order is confirmed only when all units are held and the payment is authorised; otherwise it is rejected with a reason | Must |
| FR-ORD-05 | A customer can list their orders and see each order's lines, totals, status, shipments and documents | Must |
| FR-ORD-06 | A customer can cancel an order until its first shipment is dispatched | Must |
| FR-ORD-07 | Each order keeps a timeline of its status changes with timestamps | Should |
| FR-ORD-08 | Operations can list and filter all orders by status and date | Should |
| FR-ORD-09 | A customer can request a return of delivered units within the return window | Should |
| FR-ORD-10 | A customer can cancel individual lines that are not yet dispatched | Could |

### Shipments (SHP)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-SHP-01 | An order is split into one shipment per shipping location in its allocation plan | Must |
| FR-SHP-02 | Each shipment is handed to the carrier and gets a tracking number | Must |
| FR-SHP-03 | Each shipment moves through created, dispatched and delivered, driven by carrier updates | Must |
| FR-SHP-04 | A customer sees every shipment of their order with status and tracking number | Must |
| FR-SHP-05 | Each shipment shows an estimated delivery date based on the shipping location's delivery time | Should |

### Payments (PAY)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-PAY-01 | At checkout the system authorises the order total with the payment provider | Must |
| FR-PAY-02 | When a shipment is dispatched, the system captures that shipment's amount | Must |
| FR-PAY-03 | When an order is cancelled or rejected after authorisation, the remaining authorisation is released | Must |
| FR-PAY-04 | The system can refund all or part of a captured amount | Must |
| FR-PAY-05 | Customers see the payment status of their orders; finance sees all payments and their history | Must |
| FR-PAY-06 | Provider declines, timeouts and unavailability are handled without charging twice and without leaving stock held | Must |
| FR-PAY-07 | The system never stores card data; it keeps only the provider's payment reference | Must |

### Invoices and receipts (BIL)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-BIL-01 | After each successful capture the system issues one invoice for that shipment: seller, buyer, lines, net, VAT rate, VAT amount, gross, number and dates | Must |
| FR-BIL-02 | VAT amounts are calculated per line from gross prices by the rules in BR-12 | Must |
| FR-BIL-03 | Invoice numbers are sequential without gaps within a numbering series; issued invoices never change | Must |
| FR-BIL-04 | After a refund the system issues a correction invoice that references the original invoice | Must |
| FR-BIL-05 | A customer can list and view their invoices; finance can list all documents by period | Must |
| FR-BIL-06 | A customer receives a simplified receipt per shipment | Should |
| FR-BIL-07 | Documents can be downloaded as PDF | Could |

### Web frontend (WEB)

The frontend only calls the public API and holds no business rules; catalogue editing stays in the API.

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-WEB-01 | A user can register, log in and log out in the browser | Must |
| FR-WEB-02 | A customer can browse, filter and search the catalogue; the product page shows variant availability | Must |
| FR-WEB-03 | A customer can manage the cart and check out with a saved address; the order page shows Pending until the order is Confirmed or Rejected | Must |
| FR-WEB-04 | A customer can see order history and details with shipments, tracking and documents, and cancel an order | Must |
| FR-WEB-05 | Operations can see stock per variant and location, list orders by status and record received returns | Should |
| FR-WEB-06 | Finance can list invoices and correction invoices by period | Should |

### Demand forecasting extension (FCS)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-FCS-01 | The system holds expected daily sales per variant and location for the coming days | Must (extension) |
| FR-FCS-02 | The system derives a stockout risk per variant and location from stock and expected sales | Must (extension) |
| FR-FCS-03 | Operations can select a forecast-aware allocation strategy that counts the risk of losing a sale at the shipping location | Must (extension) |
| FR-FCS-04 | When forecasts are missing or older than the freshness limit, allocation uses the average of recent sales instead | Must (extension) |
| FR-FCS-05 | Operations can view expected sales, stockout risk and forecast age per variant and location | Should (extension) |

## User stories and acceptance criteria

Fourteen stories cover the MVP and its key failure cases; each acceptance criterion becomes at least one automated test. Further stories are added per release, before its work starts.

### US-01 · Register and log in (FR-CUS-01, 02)

As a visitor, I want to create an account and log in, so that I can place and track orders.

- Given no account with my email, when I register with a valid email and password, then my account is created and my password is never returned or stored in readable form.
- Given an account with my email already exists, when I register again, then registration is refused with a clear reason.
- Given a registered account, when I log in with correct credentials, then I receive an access token with an expiry time; with wrong credentials I receive an error that does not say which field was wrong.

### US-02 · Manage delivery addresses (FR-CUS-04, 05)

As a customer, I want to keep several addresses, so that checkout is fast.

- Given I am logged in, when I add an address and mark it as default, then it is preselected at checkout and any previous default is unmarked.
- Given another customer's address, when I try to read or change it, then access is refused.

### US-03 · Maintain the catalogue (FR-CAT-01–04, 09)

As operations, I want to manage products and their variants, so that customers see a correct offer.

- Given a product, when I add a variant whose size and colour already exist for that product, then it is refused.
- Given a variant, when I archive its product, then it disappears from browsing and cannot be added to a cart, but existing orders still show it.
- Given I am a customer, when I try to change the catalogue, then access is refused.

### US-04 · Browse and filter (FR-CAT-06, 08)

As a customer, I want to filter by size and colour, so that I only see what I can buy.

- Given products in several categories, when I filter by category, size and price range, then only matching products are returned, page by page, with the total count.
- Given a variant with no available stock in any eligible location, when I view the product, then that variant shows as out of stock.

### US-05 · Receive and correct stock (FR-INV-02–04)

As operations, I want to record stock changes, so that availability is always right.

- Given a variant at a location, when I record a receipt of 10 units, then on hand and available both grow by 10 and the change appears in the history with its reason.
- Given 3 units on hand of which 2 are held, when I record a correction to 1 unit, then it is refused, because held units cannot be removed.

### US-06 · Manage the cart (FR-ORD-01)

As a customer, I want a cart, so that I can collect items before buying.

- Given an empty cart, when I add a variant twice, then the cart shows one line with quantity 2 and the current price.
- Given a price changed after I added an item, when I view the cart, then I see the new price.

### US-07 · Place an order (FR-ORD-02–04, FR-INV-05–07, FR-PAY-01)

As a customer, I want to place an order safely, so that I either get my items or know at once that I won't.

- Given a cart whose items are available, when I check out, then all units are held, the total is authorised and the order becomes Confirmed.
- Given I submit the same checkout twice with the same key, when both requests are processed, then exactly one order exists and both responses refer to it.
- Given one cart line is no longer available anywhere, when I check out, then the order is Rejected, the reason names the unavailable variant, nothing stays held and no payment is authorised.

### US-08 · No overselling under concurrency (FR-INV-07, NFR-01)

As the retailer, I want the last unit sold only once, so that no order must be cancelled for missing stock.

- Given exactly 1 available unit of a variant across all locations, when 20 customers check out that variant at the same moment, then exactly one order is Confirmed and the others are Rejected as unavailable.
- Given any sequence of orders and stock changes, then held quantity never exceeds on-hand quantity at any location.

### US-09 · Payment declined (FR-PAY-06, FR-INV-09)

As a customer, I want a clear result when my payment fails, so that I can try again.

- Given the provider declines the authorisation, when checkout completes, then the order is Rejected with reason "payment declined" and its held units are available again immediately.
- Given the provider does not answer in time, when the outcome is still unknown, then the system asks the provider for the result before deciding, and the customer is never charged for a Rejected order.

### US-10 · Hold expires (FR-INV-08, BR-04)

As the retailer, I want abandoned holds to free stock, so that items are not blocked forever.

- Given an order whose payment authorisation has not completed, when the hold time limit passes, then its units become available and the order is Rejected with reason "reservation expired".

### US-11 · Split shipments and capture (FR-SHP-01–04, FR-PAY-02, FR-BIL-01)

As a customer, I want to see each parcel of my order, so that I know what arrives when.

- Given an order allocated to two locations, when it is confirmed, then two shipments exist, each with its own lines.
- Given a shipment is dispatched, then its units leave stock, its amount is captured and one invoice for exactly that amount is issued.
- Given all shipments are delivered, then the order becomes Delivered.

### US-12 · Cancel an order (FR-ORD-06, FR-PAY-03, FR-INV-09)

As a customer, I want to cancel before dispatch, so that I am not charged for something I no longer want.

- Given a Confirmed order with no dispatched shipment, when I cancel, then it becomes Cancelled, its units are available again and the authorisation is released.
- Given an order with a dispatched shipment, when I try to cancel, then cancellation is refused and I am pointed to returns.

### US-13 · Return and refund (FR-ORD-09, FR-PAY-04, FR-BIL-04, FR-INV-14)

As a customer, I want to return items I don't keep, so that I get my money back.

- Given a delivered unit within the return window, when operations records it as received in sellable condition, then I am refunded its price, a correction invoice referencing the original invoice is issued, and the unit is back in stock at the receiving location.
- Given the return window has passed, when I request a return, then it is refused.

### US-14 · Reconcile documents (FR-BIL-03, 05, G3)

As finance, I want every money movement documented, so that the books are correct.

- Given any period, when I list documents, then the sum of invoices minus correction invoices equals the sum of captures minus refunds in that period.
- Given an issued invoice, when anyone tries to change it, then it is refused; only a correction invoice can change its effect.

## Non-functional requirements

Fifteen quality requirements are stated so that each can be checked by a test or a measurement; none names a technology. Numeric performance targets are initial values for a single developer machine and will be confirmed in the TRD.

| ID | Area | Requirement | Verified by |
| --- | --- | --- | --- |
| NFR-01 | Consistency | Held quantity never exceeds on-hand quantity for any variant and location, under any number of concurrent requests | Concurrency test (US-08) |
| NFR-02 | Idempotency | Repeating any state-changing request with the same key, or processing any internal message twice, has the same effect as doing it once | Automated tests |
| NFR-03 | Atomicity | A state change and the notification that announces it to other parts of the system are never separated: neither is lost, neither happens alone | Failure test |
| NFR-04 | Recovery | After a restart of any single component, every in-flight order finishes or is compensated without manual action | Failure test |
| NFR-05 | Isolation of failures | If invoicing or forecasting is unavailable, customers can still check out and shipments still proceed; missing documents are produced after recovery | Failure test |
| NFR-06 | Bounded waiting | When the payment provider is slow or down, checkout returns a result within 10 s and calls to it are paused after repeated failures instead of piling up | Failure test |
| NFR-07 | Responsiveness | Catalogue reads respond within 300 ms at the 95th percentile and checkout within 1 s, excluding provider delay, with 10,000 variants loaded | Load test on a developer machine |
| NFR-08 | Traceability | Every customer request can be followed through all steps it causes, across all parts of the system, by one correlation identifier | Manual check + test |
| NFR-09 | Auditability | Every order status change, stock change and money movement is recorded with time, cause and actor | Automated tests |
| NFR-10 | Security | Passwords are stored only as salted hashes; tokens expire; every endpoint checks the caller's role and data ownership; no secrets in the repository | Tests + review |
| NFR-11 | Money accuracy | Amounts are exact decimals in the store currency, rounded half-up to 0.01; every document's line sums equal its totals | Unit tests |
| NFR-12 | API usability | Every endpoint is described in a machine-readable specification with examples, uses one error format and is versioned | Specification review |
| NFR-13 | Testability | Business rules can be tested without databases, networks or external systems; every Must requirement has an automated test | Test report |
| NFR-14 | Replaceability | An allocation strategy, the payment provider, the carrier and the forecaster can each be replaced without changing order processing | Design review + tests |
| NFR-15 | Portability | The whole system starts on one developer machine with a single command, using only free tools | Fresh-machine check |

## Business rules

Seventeen rules fix the business decisions behind the requirements. Values marked "configurable" are proposals that can change without a new PRD version.

### Order life cycle

An order has seven statuses; returns are tracked per line and do not change the order status.

&#91;embedded content: order life cycle · 7 statuses\]

An order is rejected when its units cannot be held, the payment is declined or the hold expires (BR-01, BR-04, BR-10).

### Rules

| ID | Topic | Rule |
| --- | --- | --- |
| BR-01 | Acceptance | An order is accepted only if every unit of every line can be held now. There are no partial orders, backorders or pre-orders. |
| BR-02 | Prices | Prices, VAT rates and the delivery fee are fixed at checkout. Later catalogue changes do not affect the order. |
| BR-03 | Delivery fee | The customer pays one delivery fee per order, however many shipments it is split into (configurable amount). Extra parcels are the retailer's cost. |
| BR-04 | Hold time limit | Units are held for at most 15 minutes (configurable) while the payment is being authorised. If authorisation has not succeeded by then, the hold expires and the order is rejected. |
| BR-05 | Confirmed holds | Once the payment is authorised, the hold no longer expires. It ends when the shipment is dispatched (units leave stock) or the order is cancelled (units become available). |
| BR-06 | Allocation | Each line is shipped from a single location when possible. A line is split across locations only when no single eligible location has the full quantity. An order has at most 3 shipments (configurable); if more are needed, it is rejected as unavailable. |
| BR-07 | Store stock | A store ships online orders only if flagged to do so, and keeps a safety quantity per variant (configurable, default 0) that is not offered online. |
| BR-08 | Authorisation | The full order total, delivery fee included, is authorised once at checkout. |
| BR-09 | Capture | Each shipment's amount is captured when it is dispatched. The delivery fee is captured with the first dispatched shipment. If capture fails after retries, the shipment is put on hold for operations and is not dispatched. |
| BR-10 | Unknown payment outcome | If the provider's answer is lost or late, the system asks the provider for the outcome before retrying or deciding. A customer is never charged twice and never charged for a rejected or cancelled order. |
| BR-11 | Cancellation | A customer can cancel an order only until its first shipment is dispatched. Cancelling releases all holds and the remaining authorisation; no invoice is issued because nothing was captured. |
| BR-12 | VAT | Prices are gross (VAT included). Each variant has a VAT rate (default 23%). Per line: net = gross / (1 + rate), VAT = gross − net, rounded half-up to 0.01. Document totals are sums of rounded line values. |
| BR-13 | Invoice numbering | Invoices use one series per month in the format FV/YYYY/MM/NNNNN, and correction invoices a separate series KOR/YYYY/MM/NNNNN. Numbers have no gaps and are never reused. |
| BR-14 | Return window | Units can be returned within 14 days of their shipment's delivery (configurable). |
| BR-15 | Refund amount | A refund equals the gross price paid for the accepted units. The delivery fee is refunded only when every unit of the order is returned. Units received damaged are not refunded and are written off. |
| BR-16 | Correction invoice | Every refund produces exactly one correction invoice that references the original invoice and lists the returned lines with negative amounts. |
| BR-17 | Order status | The order status follows its shipments: Partially shipped when some shipments are dispatched, Shipped when all are dispatched, Delivered when all are delivered. |

## Demand forecasting extension

Forecasting is built only after the MVP and tests one hypothesis: allocation that accounts for expected local demand loses fewer sales and costs less than rule-based allocation. The core flow (hold, pay, ship, invoice) never depends on it.

**What it predicts.** Expected daily sales per variant and location for the coming days, and from that a stockout risk.

**How the product uses it.** As one factor in the allocation decision, next to shipping cost, the extra-parcel cost and the delivery promise: the expected cost of a lost sale at the location a unit is taken from (FR-FCS-03).

**When it is unavailable.** Allocation falls back to the average of recent sales, so orders are never delayed by forecasting (FR-FCS-04, NFR-05).

**How success is judged.** Forecast quality and business effect are measured separately.

| Question | Measure | Compared against |
| --- | --- | --- |
| Is the forecast better than simple rules? | Weighted absolute percentage error (WAPE) and mean absolute error (MAE) | Same day last week; moving average of recent sales |
| Does it improve fulfilment? | Order fill rate, lost sales, cost per order, parcels per order, share of orders meeting the delivery promise | Nearest location, cheapest shipping, fewest parcels, moving-average-aware allocation, and a perfect-knowledge upper bound |
| Is the difference real? | 95% confidence intervals over repeated simulation runs with different random seeds | — |

**Data.** Training uses public retail sales datasets (candidates: H&M Personalized Fashion Recommendations, M5), used under their licence terms and not stored in the repository. The location network, stock levels and orders are simulated, and the simulator runs the same allocation logic as the product.

A result showing no improvement is an acceptable outcome; the goal is a tested answer, not a guaranteed gain.

## Assumptions and constraints

The product is built by one person, runs locally and sells in one country; any assumption that proves wrong is raised as an open question and may change scope.

| ID | Assumption | If wrong |
| --- | --- | --- |
| A-01 | One retailer, selling to private customers (B2C) in one country, Poland, in one currency, PLN | VAT, invoice formats and addresses need rework |
| A-02 | The location network is simulated: a few central warehouses and a larger number of stores, with positions and delivery times | Allocation results do not transfer directly to a real network |
| A-03 | The payment provider, the carrier and the store sales feed are simulated, including declines, delays and outages | Real integrations need their own adapters and contracts |
| A-04 | Delivery is domestic only | International shipping needs new rules for fees, delivery times and VAT |
| A-05 | Public datasets can be mapped onto variants and locations; sizes and store-level sales may need to be derived synthetically | Forecast quality claims must be qualified |
| A-06 | The listed API requirements are the working definition of "key functionalities" until the instructor confirms them | Requirements are added or reprioritised |

| ID | Constraint |
| --- | --- |
| C-01 | One developer for analysis, design, implementation, testing and documentation |
| C-02 | The project must meet the course grading components and API requirements by the course deadline |
| C-03 | Only free tools; everything runs on one developer machine |
| C-04 | Every function is reachable through the API; the web frontend covers only the screens in FR-WEB and holds no business logic |
| C-05 | Dataset licences restrict use to research and education; data is not redistributed |

## Release plan

The product is delivered in five releases; each ends at a gate, and the order-to-cash MVP (R2) is the core. Dates are set once the course deadline is confirmed (Q-01).

&#91;embedded content: release roadmap · 5 releases, 4 gates\]

The next release starts only when the current one meets its exit criteria in the table below.

| Release | Scope (requirement IDs) | Exit criteria |
| --- | --- | --- |
| R0 · Foundations | PRD and TRD baselined; repository, local environment and automated checks in place | PRD v1.0 and TRD v1.0 approved; every component starts locally and reports healthy |
| R1 · Accounts and catalogue | FR-CUS-01–05, FR-CAT-01–04, 06, 09, FR-INV-01–04, FR-WEB-01–02 | US-01 to US-05 pass; API specification published; business rules unit-tested |
| R2 · Order to cash (MVP) | FR-INV-05–10, FR-ORD-01–06, FR-SHP-01–04, FR-PAY-01–07, FR-BIL-01–05, FR-WEB-03–04 | US-06 to US-12 pass; NFR-01 to NFR-04 verified; integration tests run against real infrastructure |
| R3 · After-sales and hardening | FR-ORD-07–09, FR-INV-11–14, FR-SHP-05, FR-BIL-06, FR-CAT-05, 07, 08, FR-WEB-05–06; NFR-05 to NFR-15 | US-13 and US-14 pass; failure tests pass; documentation complete |
| R4 · Demand forecasting | FR-FCS-01–05 | Forecast and simulation results reported as defined in the forecasting extension |

Could requirements (FR-CUS-06, FR-CAT-10, FR-ORD-10, FR-BIL-07) are taken only if time remains after R3.

## Course requirements mapping

Every grading component and API requirement of the course maps to requirements in this PRD; demand forecasting goes beyond the graded scope and no grade depends on it.

| Grade | Course component | Met through | Release |
| --- | --- | --- | --- |
| 3.0 | Web service | All functions exposed as a documented API (FR-\*, NFR-12) | R1 |
| 3.5 | Unit tests | Business rules tested in isolation (NFR-13, BR-01–17) | R1–R2 |
| 4.0 | Integration tests and design patterns | Tests against real infrastructure; replaceable strategies and adapters (NFR-14) | R2 |
| 4.5 | Microservices and inter-service communication | Independent components that cooperate on one order; failure isolation (NFR-03–05) | R2 |
| 5.0 | Documentation | PRD, TRD, API specifications, decision records, setup and test instructions | R3 |

| Course API requirement | Requirements |
| --- | --- |
| Services necessary for e-commerce | FR-CUS-01–02, FR-CAT-06–07, FR-ORD-01–05, FR-SHP-04 |
| Customers | FR-CUS-01–07 |
| Products | FR-CAT-01–10, FR-INV-01–04 |
| Orders | FR-ORD-01–10, FR-SHP-01–05 |
| Payments | FR-PAY-01–07 |
| Invoices and receipts | FR-BIL-01–07 |
| Key functionalities within the domains | All Must requirements, pending confirmation (A-06, Q-02) |

## Product risks

The largest risk is scope: a distributed order-to-cash flow plus a forecasting study is a lot for one person, so the release order protects the graded MVP first.

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| RSK-01 | Scope exceeds what one person can finish before the deadline | High | High | Strict release order; Should and Could items cut first; forecasting only after R3 |
| RSK-02 | Keeping stock, payment and documents consistent across components takes longer than planned | High | High | Fixed list of failure scenarios defined before R2; failure tests written with the features |
| RSK-03 | The course deadline or grading interpretation differs from assumptions | Medium | High | Confirm deadline and "key functionalities" with the instructor before R1 (Q-01, Q-02) |
| RSK-04 | Public datasets lack sizes or store-level sales | High | Medium | Derive them synthetically with documented rules; state the limits in results |
| RSK-05 | Forecast-aware allocation shows no measurable benefit | Medium | Low | A rejected hypothesis is a valid result; the core product is unaffected |
| RSK-06 | Simulated provider and carrier are too simple to exercise real failures | Medium | Medium | Configurable decline rate, delay and outage modes in both simulators |
| RSK-07 | The full system is too heavy for one developer machine | Low | Medium | Measure resource use in R0; keep the number of running components minimal |

## Open questions

Ten questions remain open; Q-01 and Q-02 block the plan and should be answered before R1 starts. Each answer updates this PRD.

- [ ] Q-01 · What is the course deadline, and are there intermediate checkpoints? Needed by R0.
- [ ] Q-02 · Does the instructor accept the API requirements in this PRD as the "key functionalities" of each domain? Needed by R1.
- [ ] Q-03 · How are operations and finance accounts created: seeded at start-up or by an administrator? Needed by R1.
- [ ] Q-04 · What is the delivery fee, and is there a free-delivery threshold? Needed by R2.
- [ ] Q-05 · What happens if a payment authorisation expires before the last shipment is dispatched? Needed by R2.
- [ ] Q-06 · Is a simplified receipt needed in addition to the invoice for every shipment, or only on request? Needed by R2.
- [ ] Q-07 · Where do customers send returns: to the shipping location only, or to any location? Needed by R3.
- [ ] Q-08 · How large is the simulated network (proposal: 2 warehouses and 8 stores)? Needed by R2.
- [ ] Q-09 · What forecast horizon and freshness limit are used (proposal: 14 days ahead, refreshed daily, stale after 48 hours)? Needed by R4.
- [ ] Q-10 · Which dataset is primary, H&M or M5, given that neither has sizes and store-level fashion sales together? Needed by R4.

## Glossary

These terms are used with exactly this meaning in the PRD, the TRD, the API and the code.

| Term | Meaning |
| --- | --- |
| Allocation plan | The decision of which location ships each unit of an order |
| Allocation strategy | A rule for building the allocation plan (nearest, cheapest, fewest parcels, forecast-aware) |
| Authorisation | The payment provider's promise to reserve an amount on the customer's payment method, without taking it yet |
| Available | On hand minus held minus safety quantity: what can still be sold online at a location |
| Capture | Taking an authorised amount, or part of it, from the customer |
| Correction invoice | A document that reverses all or part of an issued invoice after a refund |
| Eligible location | A location that is active, ships online orders and has enough available units |
| Fill rate | Share of ordered units that are shipped |
| Hold | Units set aside for one order so no other order can take them; called a reservation in technical documents |
| Idempotency key | A client-chosen value that makes a repeated request return the first result instead of acting twice |
| Location | A place that holds stock: a central warehouse or a physical store |
| Lost sale | Demand that could not be served because the variant was out of stock at that location |
| On hand | Units physically present at a location |
| Product | A clothing item as sold, for example a linen shirt, independent of size and colour |
| Refund | Returning a captured amount, or part of it, to the customer |
| Safety quantity | Units per variant a store keeps for in-person sales and never offers online |
| Shipment | The units of one order sent from one location in one parcel |
| SKU | Stock keeping unit: the unique code of one variant |
| Stockout risk | The probability that a variant runs out at a location before it is replenished, based on expected sales |
| Variant | One size and colour of a product, the unit that is stocked and sold |
