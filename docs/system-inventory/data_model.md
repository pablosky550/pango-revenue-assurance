# Data Model

## Purpose

This document defines the logical data model for the Pango Revenue Assurance platform.

The objective is to create a unified data model capable of integrating operational, payment, banking, and accounting data independently of their original source.

The model is designed to support reconciliation, anomaly detection, auditing, and financial reporting.

---

# Core Business Entities

| Entity               | Description                                                           | Source             | Priority |
| -------------------- | --------------------------------------------------------------------- | ------------------ | -------- |
| Locations            | Customer locations (cities, apartments, airports, universities, etc.) | Backend            | Critical |
| Zones                | Parking zones belonging to locations                                  | Backend            | Critical |
| Tariffs              | Pricing configuration for each zone                                   | Backend            | Critical |
| Parking Sessions     | Mobile parking transactions                                           | Backend            | Critical |
| Reservations         | Reservation transactions                                              | Backend            | High     |
| Permits              | Permit transactions                                                   | Backend            | High     |
| Violations           | Parking violation payments                                            | Backend            | High     |
| Refunds              | Refunded transactions                                                 | Backend / PayPal   | Critical |
| Disputes             | Chargebacks and disputes                                              | Backend / PayPal   | Critical |
| Statements           | Customer financial statements                                         | Backend            | Critical |
| Statement Rules      | Statement calculation rules                                           | Backend            | Critical |
| Payment Transactions | Payment processor transactions                                        | PayPal / Braintree | Critical |
| Bank Transactions    | Bank movements                                                        | FirstBank          | Critical |
| Accounting Entries   | Financial accounting records                                          | QuickBooks         | Critical |

---

# Logical Revenue Flow

Tariff
↓
Zone
↓
Location

↓

Business Event

├── Parking Session
├── Reservation
├── Permit
└── Violation

↓

Revenue

↓

Payment Processor

↓

Bank

↓

Accounting

---

# Planned Database Tables

| Table                | Source             |
| -------------------- | ------------------ |
| locations            | Backend            |
| zones                | Backend            |
| tariffs              | Backend            |
| parking_sessions     | Backend            |
| reservations         | Backend            |
| permits              | Backend            |
| violations           | Backend            |
| refunds              | Backend / PayPal   |
| disputes             | Backend / PayPal   |
| statements           | Backend            |
| statement_rules      | Backend            |
| payment_transactions | PayPal / Braintree |
| bank_transactions    | FirstBank          |
| accounting_entries   | QuickBooks         |

---

# Planned Relationships

| Parent              | Child               |
| ------------------- | ------------------- |
| Location            | Zone                |
| Zone                | Tariff              |
| Zone                | Parking Session     |
| Parking Session     | Payment Transaction |
| Reservation         | Payment Transaction |
| Permit              | Payment Transaction |
| Violation           | Payment Transaction |
| Payment Transaction | Bank Transaction    |
| Bank Transaction    | Accounting Entry    |
| Statement           | Location            |
| Statement Rule      | Statement           |

---

# Revenue Assurance Reconciliation Layers

| Layer                       | Source             |
| --------------------------- | ------------------ |
| Operational Layer           | Backend            |
| Financial Calculation Layer | Backend            |
| Statement Layer             | Backend            |
| Payment Processor Layer     | PayPal / Braintree |
| Banking Layer               | FirstBank          |
| Accounting Layer            | QuickBooks         |

---

# Planned Reconciliation Pipeline

Parking Session
↓
Payment Transaction
↓
Bank Transaction
↓
Accounting Entry

Reservation
↓
Payment Transaction
↓
Bank Transaction
↓
Accounting Entry

Permit
↓
Payment Transaction
↓
Bank Transaction
↓
Accounting Entry

Violation
↓
Payment Transaction
↓
Bank Transaction
↓
Accounting Entry

---

# Future Data Sources

| Source     | Status    |
| ---------- | --------- |
| Backend    | Available |
| PayPal     | Available |
| FirstBank  | Available |
| Braintree  | Partial   |
| QuickBooks | Pending   |
