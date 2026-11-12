# Value Objects and strongly typed identifiers

## Value Objects

| Value Object | Attributes (types) | Self-validation: rejected at creation | Operation returning a new instance | Board source |
| --- | --- | --- | --- | --- |
| `Money` | `amount: Decimal`, `currency: str` | negative amount; more than 2 decimal places; currency that is not a 3-letter upper-case ISO code (e.g. `"zl"`, `""`) → `InvalidMoneyException`. A product price must also be above zero; `Product` checks this on "Set price" (`InvalidPriceException`) | `add(other: Money) -> Money` (different currency → `CurrencyMismatchException`); `multiply(quantity: Quantity) -> Money` for a line total | "Set price", "Price rejected, must be above zero", "Order total with delivery fee", "prices include VAT" |
| `Quantity` | `value: int` | `0`, negative numbers, more than `5` → `InvalidQuantityException` | `add(other: Quantity) -> Quantity`: merging the same size and colour gives a new `Quantity`; a sum above 5 → `QuantityLimitExceededException` | "Item rejected, quantity must be above zero", "Is there a limit per item?" → "at most 5 units of one size and colour per order", "quantities of the same size and colour are added together" |
| `Sku` | `code: str` | empty or whitespace-only code; code containing spaces → `InvalidSkuException`. The code is stored upper-case (`"dress-red-m"` → `"DRESS-RED-M"`) | `Sku.parse(raw: str) -> Sku` always builds a new normalised object. There is no setter: a different size or colour is a different `Sku` | "What identifies a variant?" → "one SKU per product, size and colour. The SKU never changes, even if the product is renamed" |
| `DeliveryAddress` | `street: str`, `postal_code: str`, `city: str`, `country_code: str` | `country_code` other than `"PL"`; postal code not in the `NN-NNN` format; empty street or city → `AddressOutsideDeliveryCountryException` / `InvalidAddressException` | Nothing is edited in place. "Choose delivery address and option" replaces the whole object on the `Cart`: `cart.choose_delivery(address: DeliveryAddress, option)`. `Order` keeps its own copy | "Address rejected, outside the delivery country", "Poland only in the first version", "Every order keeps its own copy of the address it was placed with" |
| `VatRate` | `percent: Decimal` | below `0` or above `100` → `InvalidVatRateException` | `vat_part_of(gross: Money) -> Money` returns a new `Money` with the VAT contained in a gross price | "How is VAT calculated?" → "prices include VAT; VAT is worked out per invoice line with the product's VAT rate on the issue date" |
| `ReturnWindow` (date pair) | `delivered_at: datetime` (UTC), `days: int = 14` | naive datetime (no time zone); `days <= 0` → `InvalidReturnWindowException` | `closes_at() -> datetime`, `contains(requested_at: datetime) -> bool`; the window object itself never changes | "How long can a customer return items?" → "14 days from delivery of each shipment, item by item" |
| `PaymentDeadline` (date pair) | `reserved_at: datetime` (UTC), `minutes: int = 15` | naive datetime; `minutes <= 0` → `InvalidPaymentDeadlineException` | `expires_at() -> datetime`, `is_expired(now: datetime) -> bool` | "How long does a reservation live without payment?" → "15 minutes to pay", actor "Time: 15 minutes after reserving" |
| `StockLevel` | `on_hand: int`, `reserved: int`, `safety_buffer: int` | negative values; `reserved` greater than `on_hand - safety_buffer` → `InvalidStockLevelException` | `reserve(quantity: Quantity) -> StockLevel` and `release(quantity: Quantity) -> StockLevel` return a new level; `available_online() -> int` | "Available online = on hand minus reserved minus the store safety buffer", "Reserve stock for order", "Release reservation", "a store keeps a safety buffer of 1 unit per size and colour" |

Equality is structural for all of them: `Money(Decimal("199.00"), "PLN") == Money(Decimal("199.00"), "PLN")`, and two `Sku("DRESS-RED-M")` are the same variant. None of them has its own id.

## Strongly typed identifiers

Each aggregate root gets its own id type, a frozen wrapper over `UUID` (e.g. `OrderId(value: UUID)` with `OrderId.new()`). Mixing them up then fails the type check (`mypy --strict`). Example: `Payment(order_id=cart.id)` is rejected because `CartId` is not `OrderId`. With raw `UUID` both would be accepted.

| Identifier | Aggregate root | Bounded context |
| --- | --- | --- |
| `UserId` | `User` | User |
| `CartId` | `Cart` | Ordering |
| `OrderId` | `Order` | Ordering |
| `ProductId` | `Product` | Ordering (catalogue) |
| `CategoryId` | `Category` | Ordering (catalogue) |
| `ReturnId` | `Return` | Ordering |
| `LocationId` | `Location` | Inventory |
| `StockItemId` | `StockItem` | Inventory |
| `StockReservationId` | `StockReservation` | Inventory |
| `PaymentId` | `Payment` | Payments |
| `ShipmentId` | `Shipment` | Shipping |
| `ReturnParcelId` | `ReturnParcel` | Shipping |
| `InvoiceId` | `Invoice` | Billing |
