-- One logical database per service on a single local server (ADR-001).
-- Runs once, when the data volume is created.
CREATE DATABASE customers_db;
CREATE DATABASE catalog_db;
CREATE DATABASE inventory_db;
CREATE DATABASE orders_db;
CREATE DATABASE payments_db;
CREATE DATABASE billing_db;
