# Financial Architecture

## Core Financial Structure

### Account 2084 — Payroll Account

Purpose:

Payroll operations account.

Revenue Assurance Priority:

Low

Reason:

Does not receive customer revenue directly. Used to process payroll, payroll taxes, wage payments, and related payroll operations.

---

### Account 2092 — Primary Revenue & Operations Account

Purpose:

Primary operational account and central treasury account for Mobile Smart City / Pango operations.

Revenue Assurance Priority:

CRITICAL

Reason:

This account receives the majority of operational revenue and distributes funds across the organization.

---

### Account 1523 — Treasury Settlement Account

Purpose:

Treasury and settlement account used to manage large outgoing payments.

Observed Sources:

* Transfers from 2092
* Transfers from 7922
* Interest income

Observed Uses:

* Payments to cities
* Payments to MP

Revenue Assurance Priority:

Medium

Reason:

Does not collect customer revenue directly but acts as a treasury hub that redistributes operational funds.

---

### Account 7922 — Municipal & Partner Operations Account

Purpose:

Operational account used for municipal, partner, merchant settlement, and third-party transactions.

Revenue Assurance Priority:

Medium

Reason:

Receives operational revenue streams, merchant settlements, external wire transfers, and partner-related payments.

Observed Sources:

* Merchant Bankcard Deposits
* Mobile Deposits
* Incoming Wire Transfers
* International Wire Transfers
* Intuit Deposits

Observed Counterparties:

* Corporation of Hamilton
* Bermuda Skyport Corporation Ltd
* JAJOMAR SA de CV
* Town of Stratford
* La Salle University

Observed Uses:

* Transfers to account 1523
* Payments to MP
* Utility payments
* Vendor payments
* Operational expenses

---

## Observed Revenue Sources

### PayPal

Observed as:

* PAYPAL TRANSFER

Role:

Settlement of customer parking transactions.

Status:

Confirmed.

### Braintree

Observed as:

* BRAINTREE FUNDING

Role:

Primary payment settlement processor.

Status:

Confirmed.

### Heartland Payment Systems

Observed as:

* HRTLAND PMT SYS

Role:

Payment processing infrastructure.

Status:

Confirmed.

### American Express

Observed as:

* AMERICAN EXPRESS SETTLEMENT

Role:

Card settlement processing.

Status:

Confirmed.

### Bankcard Deposits

Observed as:

* BANKCARD DEP
* BANKCARD MERCH DEP

Role:

Card acquiring settlements.

Status:

Confirmed.

---

## Observed Internal Flows

### Account 2092 → Account 2084

Purpose:

Payroll funding.

Evidence:

Transfers observed from 2092 funding payroll-related operations.

Status:

Confirmed.

### Account 2092 → Account 1523

Purpose:

Treasury settlement and cash management.

Evidence:

Transfers observed from 2092 to account 1523.

Status:

Confirmed.

### Account 7922 → Account 1523

Purpose:

Treasury funding and settlement support.

Evidence:

Transfers observed from account 7922 to account 1523.

Status:

Confirmed.

---

## Major Operational Outflows

Observed categories:

* Payroll funding
* Payments to cities
* Payments to MP
* Vendor payments
* Loan payments (SBA)
* Principal Financial payments
* Treasury transfers
* Check payments

---

## Current Understanding of Financial Flow

Customer
↓
Pango Products
│
├──> Mobile Payments
├──> Reservations
├──> Permits
├──> Pay Ticket
├──> Merchant Club
└──> Other Services

↓
Payment Processors
│
├──> PayPal
├──> Braintree
├──> Heartland
├──> American Express
└──> Card Networks

↓
Account 2092
(Primary Revenue & Operations Account)

│
├──> Account 2084 (Payroll)
├──> Account 1523 (Treasury Settlement)
├──> Vendors
├──> Loans
├──> Operating Expenses
└──> Other Operational Payments


ACCOUNT 2084
(Payroll)

│
├──> Employees
├──> Payroll taxes
├──> ADP


MUNICIPAL / PARTNER REVENUE

├──> Corporation of Hamilton
├──> Bermuda Skyport
├──> JAJOMAR
├──> Town of Stratford
└──> Other Partners

↓
Account 7922
(Municipal & Partner Operations)

│
├──> Merchant Settlements
├──> International Partners
├──> Municipal Payments
├──> Third-Party Operations
└──> Treasury Transfers│
└──> Account 1523 (Treasure Settlement)

↓
Account 1523
(Treasury Settlement Account)

│
├──> Cities
├──> MP
└──> Other Large Settlement Payments

# Bank Account Flow

2092
│
├──→ 2084
│
└──→ 1523

7922
│
└──→ 1523

1523
│
├──→ Cities
└──→ MP

---

## Revenue Assurance Scope

Phase I Focus:

1. Payment Processors → Account 2092
2. Account 2092 → Payroll Funding
3. Account 2092 → Treasury Settlement (1523)
4. Account 2092 → Accounting / QuickBooks
5. Treasury Settlement (1523) → Cities / MP

Current Status:

Financial architecture partially validated through bank statement analysis.

Pending validation through:

* Backend exports
* Braintree reports
* PayPal reports
* QuickBooks exports