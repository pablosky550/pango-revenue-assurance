# Backend Structure

## Purpose

This document describes the structure of the Pango Administration Backend (PRD) and identifies the operational modules relevant for Revenue Assurance.

The backend is the primary operational source of truth for parking activity, permits, reservations, violations, payments, refunds, disputes, locations, and reporting.

---

## Backend Modules

| Area                    | Module                 | Revenue Assurance Relevance | Status         |
| ----------------------- | ---------------------- | --------------------------- | -------------- |
| Monitoring              | LPR Monitoring         | Medium                      | Pending Review |
| Monitoring              | Hotlist Alerts         | Low                         | Pending Review |
| Monitoring              | WhiteList              | Low                         | Pending Review |
| Monitoring              | Contact List           | Low                         | Pending Review |
| PMC Business            | Dashboard              | Medium                      | Pending Review |
| PMC Business            | Codes List             | Medium                      | Pending Review |
| PMC Business            | Coupons                | High                        | Pending Review |
| Enforcement             | Tickets List           | High                        | Pending Review |
| Enforcement             | Add Payment            | High                        | Pending Review |
| Enforcement             | License Plate Check    | Medium                      | Pending Review |
| Enforcement             | Resident Permits       | High                        | Pending Review |
| Enforcement             | Tire Chalking          | Low                         | Pending Review |
| Mobility & Traffic Mgmt | Occupancy              | Medium                      | Pending Review |
| Mobility & Traffic Mgmt | Counter                | Medium                      | Pending Review |
| Pulse BI Reports        | Pulse Dashboard MSC    | Critical                    | Pending Review |
| Pulse BI Reports        | Pulse Dashboard        | Critical                    | Pending Review |
| Pulse BI Reports        | BI General             | Critical                    | Pending Review |
| Pulse BI Reports        | BI Mobile Payments     | Critical                    | Pending Review |
| Pulse BI Reports        | BI Permits             | Critical                    | Pending Review |
| Pulse BI Reports        | BI Pay Violations      | Critical                    | Pending Review |
| Reports Real-time       | Parking Transactions   | Critical                    | Pending Review |
| Reports Real-time       | Finance                | Critical                    | Pending Review |
| Reports Real-time       | General Finance        | Critical                    | Pending Review |
| Reports Real-time       | Executive Summary      | Critical                    | Pending Review |
| Reports Real-time       | Permits                | High                        | Pending Review |
| Reports Real-time       | Reservations           | High                        | Pending Review |
| Reports Real-time       | Refunds                | Critical                    | Pending Review |
| Reports Real-time       | Disputes               | Critical                    | Pending Review |
| Reports Real-time       | Statements             | Critical                    | Pending Review |
| Administration          | Cities                 | High                        | Pending Review |
| Administration          | Zones                  | High                        | Pending Review |
| Administration          | Tariff Management      | Critical                    | Pending Review |
| Administration          | Refunds & Disputes     | Critical                    | Pending Review |
| Administration          | Permit Management      | High                        | Pending Review |
| Administration          | Reservation Management | High                        | Pending Review |
| Administration          | Location Manager       | High                        | Pending Review |
| Administration          | Statements Manager     | Critical                    | Pending Review |
| Administration          | Audit                  | Critical                    | Pending Review |

---

## Priority Review Order

### Tier 1 - Critical

1. BI Mobile Payments
2. Parking Transactions
3. Finance
4. General Finance
5. Executive Summary
6. Statements
7. Statements Manager
8. Refunds
9. Disputes
10. Audit

### Tier 2 - High

1. BI Permits
2. Permit Management
3. Reservation Management
4. Tickets List
5. Cities
6. Zones
7. Tariff Management

### Tier 3 - Medium

1. Occupancy
2. Counter
3. License Plate Checks
4. Coupons

---

## Revenue Assurance Objective

Identify how operational events are generated and transformed into:

Location Activity
→ Revenue
→ Settlement
→ Bank Deposit
→ Accounting Entry

The backend is expected to provide the operational layer required to validate the revenue lifecycle end-to-end.

## Backend Discoveries

## Backend Discoveries

### Confirmed Business Entities

| Entity            | Status             | Source Module        |
| ----------------- | ------------------ | -------------------- |
| Location          | Confirmed          | BI Mobile Payments   |
| Zone              | Confirmed          | Parking Transactions |
| Parking Session   | Confirmed          | BI Mobile Payments   |
| Parking Extension | Confirmed          | BI Mobile Payments   |
| Revenue           | Confirmed          | BI Mobile Payments   |
| Transaction Fee   | Confirmed          | BI Mobile Payments   |
| Owner Revenue     | Confirmed          | BI Mobile Payments   |
| Pango Revenue     | Confirmed          | BI Mobile Payments   |
| Statement         | Confirmed          | Statements           |
| Vehicle Plate     | Confirmed          | Parking Transactions |
| User Account      | Confirmed          | Parking Transactions |
| Permit            | Pending Validation | Permit Modules       |
| Reservation       | Pending Validation | Reservation Modules  |
| Refund            | Pending Validation | Refund Modules       |
| Dispute           | Pending Validation | Dispute Modules      |

---

### Confirmed Revenue Metrics

| Metric                   | Confirmed |
| ------------------------ | --------- |
| Total Parking Sessions   | Yes       |
| Parking Extensions       | Yes       |
| Total Parking Receipts   | Yes       |
| Transaction Fee          | Yes       |
| Owner Revenue            | Yes       |
| Pango Revenue            | Yes       |
| Net Receipts             | Yes       |
| Average Ticket           | Yes       |
| Average Session Duration | Yes       |

---

### Confirmed Reporting Outputs

| Output                 | Confirmed |
| ---------------------- | --------- |
| Location Statements    | Yes       |
| Revenue Summaries      | Yes       |
| Session Reports        | Yes       |
| Mobile Payment Reports | Yes       |
| Financial Reports      | Partial   |

---

### Confirmed Revenue Flow

Parking Session
→ Revenue
→ Transaction Fee
→ Owner Revenue / Pango Revenue
→ Statement
→ Payment Processor
→ Bank
→ Accounting

Status:

Partially validated through backend and banking analysis.

---

### Key Findings

1. Location statements are generated from backend operational data.

2. Revenue is calculated at session level and aggregated at location level.

3. Revenue sharing calculations are performed within the platform.

4. Transaction fee calculations are available at location level.

5. Operational activity and financial activity appear linked through a common reporting structure.

6. The backend contains sufficient data to support end-to-end Revenue Assurance validation.


### Confirmed Statement Generation Process

#### Statements Module

Status:

Confirmed.

Description:

The backend contains a dedicated Statements module capable of generating and distributing customer statements.

Observed Features:

| Feature                   | Status    |
| ------------------------- | --------- |
| Statement Repository      | Confirmed |
| Statement Download        | Confirmed |
| Statement History         | Confirmed |
| Monthly Statements        | Confirmed |
| Weekly Statements         | Confirmed |
| Location-Based Statements | Confirmed |
| Date Filtering            | Confirmed |
| Multi-Location Support    | Confirmed |

---

### Statement Granularity

| Statement Type      | Observed |
| ------------------- | -------- |
| Weekly Statements   | Yes      |
| Monthly Statements  | Yes      |
| Location Statements | Yes      |

Examples Observed:

* Village of Scarsdale, NY (Weekly)
* Harbor Place, MD (Monthly)
* Parke Laurel, MD (Monthly)
* High Pointe, VA (Monthly)
* Preserve at Owings, MD (Monthly)

---

### Confirmed Reporting Hierarchy

Operational Activity
→ Session
→ Revenue Calculation
→ Revenue Sharing
→ Statement Generation
→ Customer Statement

Status:

Confirmed through backend analysis.

---

### Revenue Assurance Implications

The Statements module appears to be the official reporting layer presented to customers.

Any Revenue Assurance validation should ultimately reconcile:

Operational Transactions
→ Financial Calculations
→ Generated Statement

This makes the Statements module one of the most critical validation points within the platform.

---

### Key Discovery

The location statements previously received are not external reports.

They are generated directly from the Pango operational platform.

This confirms that:

Backend
→ Statement

is a validated relationship within the revenue lifecycle.

### Refund Management Module

Status:

Confirmed.

Description:

The backend contains a dedicated refund reporting and management module.

Observed Features:

| Feature                 | Status    |
| ----------------------- | --------- |
| Refund Repository       | Confirmed |
| Refund Search           | Confirmed |
| Refund Date Filtering   | Confirmed |
| Location Filtering      | Confirmed |
| Charge Result Filtering | Confirmed |
| Refund Amount Tracking  | Confirmed |
| Processor Fee Tracking  | Confirmed |
| Refund Payment Tracking | Confirmed |
| Refund Status Tracking  | Confirmed |

---

### Refund Data Model

| Field          | Observed |
| -------------- | -------- |
| User           | Yes      |
| Date           | Yes      |
| Account        | Yes      |
| Amount         | Yes      |
| Processor Fee  | Yes      |
| Refund Type    | Yes      |
| Description    | Yes      |
| Location       | Yes      |
| Refund Payment | Yes      |
| Charge Result  | Yes      |
| Funding Source | Yes      |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

Refunds directly impact:

* Revenue
* Net Receipts
* Owner Revenue
* Pango Revenue
* Processor Settlement
* Bank Reconciliation

Any discrepancy between refunds recorded in the backend and refunds processed by payment processors may result in revenue leakage or reconciliation differences.

---

### Validation Objectives

| Validation                     | Status  |
| ------------------------------ | ------- |
| Refund → Original Transaction  | Pending |
| Refund → Payment Processor     | Pending |
| Refund → Settlement Adjustment | Pending |
| Refund → Bank Impact           | Pending |
| Refund → Accounting Entry      | Pending |

---

### Key Observation

The platform tracks refund amounts and associated processor fees separately.

This suggests that refund-related processor costs can be analyzed independently from the refunded transaction amount.

This may become a significant Revenue Assurance control point.


### Dispute Management Module

Status:

Confirmed.

Description:

The backend contains a dedicated dispute management module for tracking payment disputes and chargeback-related activity.

Observed Features:

| Feature                      | Status    |
| ---------------------------- | --------- |
| Dispute Repository           | Confirmed |
| Charge Date Tracking         | Confirmed |
| Dispute Date Tracking        | Confirmed |
| Response Deadline Tracking   | Confirmed |
| Resolution Date Tracking     | Confirmed |
| Dispute Amount Tracking      | Confirmed |
| Location Association         | Confirmed |
| Merchant Association         | Confirmed |
| Customer Account Association | Confirmed |
| Status Tracking              | Confirmed |
| Account Blocking Capability  | Confirmed |

---

### Dispute Data Model

| Field         | Observed |
| ------------- | -------- |
| Dispute ID    | Yes      |
| Charge Date   | Yes      |
| Disputed On   | Yes      |
| Respond By    | Yes      |
| Resolved Date | Yes      |
| Amount        | Yes      |
| Location      | Yes      |
| Status        | Yes      |
| Merchant      | Yes      |
| Account       | Yes      |
| Customer Name | Yes      |
| Blocked Flag  | Yes      |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

Disputes represent one of the highest-risk revenue leakage areas because they directly impact:

* Revenue Recognition
* Processor Settlement
* Net Receipts
* Owner Revenue
* Pango Revenue
* Accounting Reconciliation

---

### Validation Objectives

| Validation                     | Status  |
| ------------------------------ | ------- |
| Dispute → Original Transaction | Pending |
| Dispute → Processor Chargeback | Pending |
| Dispute → Revenue Adjustment   | Pending |
| Dispute → Settlement Impact    | Pending |
| Dispute → Accounting Entry     | Pending |
| Dispute Resolution Tracking    | Pending |

---

### Refund vs Dispute

| Refund                            | Dispute                                   |
| --------------------------------- | ----------------------------------------- |
| Initiated by customer or operator | Initiated by cardholder through processor |
| Usually voluntary                 | Usually involuntary                       |
| Known immediately                 | Can occur weeks later                     |
| Direct transaction adjustment     | Chargeback workflow                       |
| Revenue reduction                 | Revenue reduction + dispute risk          |

---

### Key Observation

The platform manages disputes as a separate operational entity rather than treating them as standard refunds.

This indicates that Revenue Assurance controls must independently validate:

* Refunds
* Disputes
* Chargebacks

as separate financial workflows.


### Tariff Management Module

Status:

Confirmed.

Description:

The Tariff Management module controls the pricing logic used to calculate parking charges.

This module represents the origin of revenue generation within the platform.

---

### Tariff Data Model

| Field             | Confirmed |
| ----------------- | --------- |
| Zone Code         | Yes       |
| Zone Name         | Yes       |
| Realtime Flag     | Yes       |
| Space Capacity    | Yes       |
| Transaction Fee   | Yes       |
| Base Price        | Yes       |
| Charging Interval | Yes       |
| Minimum Time      | Yes       |
| Maximum Time      | Yes       |
| Initial Charge    | Yes       |
| Maximum Charge    | Yes       |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

All parking revenue calculations originate from tariff configuration.

Incorrect tariff configuration can directly impact:

* Revenue
* Statements
* Owner Revenue
* Pango Revenue
* Bank Reconciliation
* Accounting

---

### Validation Objectives

| Validation               | Status  |
| ------------------------ | ------- |
| Tariff → Session Charge  | Pending |
| Session Charge → Revenue | Pending |
| Revenue → Statement      | Pending |
| Revenue → Bank           | Pending |

---

### Key Observation

Tariffs are configured at zone level.

Revenue Assurance validation should include periodic verification that operational tariffs match contractual tariff definitions.

### Audit Module

Status:

Confirmed.

Description:

The Audit module tracks changes performed within the platform.

The module provides traceability for operational and configuration changes.

---

### Audit Data Model

| Field          | Confirmed |
| -------------- | --------- |
| User Name      | Yes       |
| Change Date    | Yes       |
| Modified Field | Yes       |
| Previous Value | Yes       |
| New Value      | Yes       |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

Audit data provides the ability to investigate discrepancies between:

* Operational Activity
* Statements
* Revenue Calculations
* Processor Settlements
* Accounting Records

---

### Validation Objectives

| Validation                   | Status  |
| ---------------------------- | ------- |
| Tariff Change Tracking       | Pending |
| Revenue Rule Change Tracking | Pending |
| Zone Configuration Tracking  | Pending |
| User Activity Tracking       | Pending |

---

### Key Observation

The platform maintains historical records of configuration changes.

This provides an important control mechanism for investigating revenue anomalies and reconciliation differences.

### Cities Module

Status:

Confirmed.

Description:

The Cities module functions as the primary customer and location management layer within the platform.

Despite the name, entities include municipalities, residential communities, apartment complexes, universities, and other customer-operated parking programs.

---

### City Data Model

| Field                           | Confirmed |
| ------------------------------- | --------- |
| City ID                         | Yes       |
| Customer / Location Name        | Yes       |
| Geographic Coordinates          | Yes       |
| Zone Assignment                 | Yes       |
| Picture Upload Configuration    | Yes       |
| Zone Bank Account Configuration | Yes       |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

All operational and financial activity is ultimately associated with a customer location.

Revenue, statements, settlements, and reporting appear to be organized at this level.

---

### Key Observation

The term "City" should be interpreted as a customer location rather than strictly as a municipality.

The module contains municipalities, residential communities, apartment complexes, and other parking customers.


### Zones Module

Status:

Confirmed.

Description:

Zones represent the operational parking areas where parking activity occurs.

Zones belong to a customer location and are associated with tariff definitions.

---

### Zone Data Model

| Field                   | Confirmed |
| ----------------------- | --------- |
| Zone ID                 | Yes       |
| Zone Code               | Yes       |
| Zone Name               | Yes       |
| Assigned Administrators | Yes       |
| Zone Location           | Yes       |

---

### Confirmed Operational Hierarchy

Customer Location
→ Zone
→ Tariff
→ Session
→ Revenue
→ Statement

Status:

Confirmed through backend analysis.

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

Parking sessions are generated at zone level.

All revenue calculations originate from activity occurring within individual zones.

---

### Key Observation

Zones are the lowest operational level currently identified within the revenue generation process.

Revenue Assurance validation will likely require reconciliation at zone level before aggregation to location, statement, bank, and accounting levels.

### Reservation Management Module

Status:

Confirmed.

Description:

The Reservation Management module manages future parking reservations and recurring reservation-based parking products.

Reservations appear to be treated as independent business entities rather than standard parking sessions.

---

### Reservation Data Model

| Field            | Confirmed |
| ---------------- | --------- |
| Reservation ID   | Yes       |
| Vehicle          | Yes       |
| Reservation Name | Yes       |
| Space            | Yes       |
| Account          | Yes       |
| Driver           | Yes       |
| Active From      | Yes       |
| Active Until     | Yes       |
| Charge           | Yes       |
| Convenience Fee  | Yes       |
| Status           | Yes       |
| Auto Renew       | Yes       |
| Active Flag      | Yes       |
| Timestamp        | Yes       |

---

### Revenue Assurance Relevance

Priority:

High

Reason:

Reservations generate revenue independently from parking sessions and may involve:

* Advance payments
* Recurring charges
* Auto-renewal logic
* Reservation-specific fees

---

### Validation Objectives

| Validation                         | Status  |
| ---------------------------------- | ------- |
| Reservation → Charge               | Pending |
| Reservation → Convenience Fee      | Pending |
| Reservation → Statement            | Pending |
| Reservation → Processor Settlement | Pending |
| Reservation → Bank                 | Pending |
| Reservation → Accounting           | Pending |

---

### Key Observation

Reservations contain their own revenue attributes including charges and convenience fees.

This suggests that reservation revenue should be reconciled separately from standard mobile parking transactions.

Auto-renew functionality introduces additional Revenue Assurance risk due to recurring billing behavior.

### Permit Management Module

Status:

Confirmed.

Description:

The Permit Management module manages long-term parking rights assigned to users and vehicles.

Permits appear to be managed as independent business entities with their own lifecycle, billing logic, and renewal process.

---

### Permit Data Model

| Field           | Confirmed |
| --------------- | --------- |
| Permit ID       | Yes       |
| Vehicle         | Yes       |
| Permit Name     | Yes       |
| Space           | Yes       |
| Account         | Yes       |
| Driver          | Yes       |
| Active From     | Yes       |
| Active Until    | Yes       |
| Charge          | Yes       |
| Convenience Fee | Yes       |
| Status          | Yes       |
| Auto Renew      | Yes       |
| Active Flag     | Yes       |
| Timestamp       | Yes       |

---

### Revenue Assurance Relevance

Priority:

High

Reason:

Permits represent recurring and contract-based revenue streams that may generate revenue independently from parking sessions.

Permit revenue may involve:

* Monthly billing
* Recurring renewals
* Permit-specific fees
* Vehicle assignment management

---

### Validation Objectives

| Validation                    | Status  |
| ----------------------------- | ------- |
| Permit → Charge               | Pending |
| Permit → Convenience Fee      | Pending |
| Permit → Statement            | Pending |
| Permit → Processor Settlement | Pending |
| Permit → Bank                 | Pending |
| Permit → Accounting           | Pending |

---

### Permit Revenue Flow

Permit
→ Charge
→ Convenience Fee
→ Revenue
→ Statement
→ Processor Settlement
→ Bank
→ Accounting

Status:

Partially validated through backend analysis.

---

### Key Observation

Permits and Reservations share a highly similar operational structure.

This suggests that both products may rely on a common billing and renewal framework within the platform.

Auto-renew functionality should be considered a high-risk Revenue Assurance control point due to recurring billing behavior.

### BI Permits Module

Status:

Confirmed.

Description:

The BI Permits module provides analytical reporting for permit-related activity and permit-generated revenue.

The module aggregates permit transactions and provides financial and operational metrics at location level.

---

### Permit Analytics Metrics

| Metric                    | Confirmed |
| ------------------------- | --------- |
| Total Permits Revenue     | Yes       |
| Total Permit Sessions     | Yes       |
| Net Permit Revenue        | Yes       |
| Transaction Fee Permits   | Yes       |
| Average Permit Ticket     | Yes       |
| Average Net Permit Ticket | Yes       |
| Historical Comparisons    | Yes       |
| Location-Level Reporting  | Yes       |

---

### Permit Revenue Data Model

| Entity                 | Confirmed |
| ---------------------- | --------- |
| Permit                 | Yes       |
| Permit Revenue         | Yes       |
| Permit Sessions        | Yes       |
| Permit Transaction Fee | Yes       |
| Vehicle                | Yes       |
| Account                | Yes       |
| Auto Renew             | Yes       |
| Active Status          | Yes       |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

Permit revenue is generated independently from mobile parking sessions and reservation activity.

Permit reconciliation will require validation across:

* Permit Transactions
* Permit Revenue
* Statements
* Payment Processors
* Bank Deposits
* Accounting Records

---

### Confirmed Permit Revenue Flow

Permit
→ Permit Charge
→ Permit Revenue
→ Statement
→ Payment Processor
→ Bank
→ Accounting

Status:

Partially validated through backend analysis.

---

### Key Observation

Permits represent a separate revenue stream with significantly higher average transaction values than standard mobile parking sessions.

Revenue Assurance controls should treat permit activity independently from mobile payments and reservations.


### General Finance Module

Status:

Confirmed.

Description:

The General Finance module consolidates financial information across all major Pango revenue streams.

This module represents the highest-level financial aggregation layer identified within the operational platform.

---

### Financial Revenue Streams

| Revenue Stream  | Confirmed |
| --------------- | --------- |
| Mobile Payments | Yes       |
| Permits         | Yes       |
| Reservations    | Yes       |
| Pango+          | Yes       |
| PMC             | Yes       |

---

### Financial Metrics

| Metric                             | Confirmed |
| ---------------------------------- | --------- |
| Total Parking Sessions             | Yes       |
| Total Parking Receipts             | Yes       |
| Convenience Fee (User Paid)        | Yes       |
| Convenience Fee (City Percentage)  | Yes       |
| Convenience Fee (City Transaction) | Yes       |
| Total Transaction Fee              | Yes       |
| Total Validated Charge             | Yes       |
| Total Net Receipts                 | Yes       |
| Average Ticket                     | Yes       |
| Total Revenue                      | Yes       |
| Owner Revenue                      | Yes       |
| Pango Revenue                      | Yes       |
| Total Net Revenue                  | Yes       |
| Total Net Revenue MSC              | Yes       |

---

### Revenue Aggregation Hierarchy

Mobile Payments
↓
Permits
↓
Reservations
↓
Pango+
↓
PMC

↓

General Finance

Status:

Confirmed.

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

This module aggregates the financial outputs of multiple operational revenue streams and provides a consolidated view of platform revenue.

The module is expected to become a primary reconciliation point between:

* Operational Activity
* Statements
* Payment Processors
* Bank Deposits
* Accounting Records

---

### Key Observation

General Finance appears to be the closest operational representation of how revenue is aggregated before external financial reconciliation.

This module should become one of the primary validation layers in the Revenue Assurance framework.

### BI Pay Violations Module

Status:

Confirmed.

Description:

The BI Pay Violations module provides analytical reporting for parking violation payments and citation-related revenue.

This module represents a dedicated revenue stream independent from standard parking sessions, permits, and reservations.

---

### Violation Data Model

| Field             | Confirmed |
| ----------------- | --------- |
| Location          | Yes       |
| License Plate     | Yes       |
| Date Range        | Yes       |
| Violation Payment | Yes       |

---

### Revenue Assurance Relevance

Priority:

High

Reason:

Violation payments generate revenue independently from parking activity and may involve:

* Citation Payments
* Administrative Fees
* Disputes
* Payment Adjustments
* Enforcement Programs

---

### Expected Revenue Flow

Violation
→ Payment
→ Revenue
→ Statement
→ Payment Processor
→ Bank
→ Accounting

Status:

Partially validated through backend analysis.

---

### Key Observation

The platform treats parking violations as an independent business process with dedicated reporting capabilities.

This confirms that citation revenue should be reconciled separately from:

* Mobile Payments
* Reservations
* Permits


### Statements Manager Module

Status:

Confirmed.

Description:

The Statements Manager module appears to manage the financial rules and configuration used to generate customer statements.

Unlike the Statements reporting module, this component appears to define how statement calculations are performed.

---

### Statement Configuration Data Model

| Field             | Confirmed |
| ----------------- | --------- |
| Location          | Yes       |
| Statement Name    | Yes       |
| From Date         | Yes       |
| To Date           | Yes       |
| Period            | Yes       |
| Amount            | Yes       |
| Calculated Flag   | Yes       |
| Calculation Basis | Yes       |
| Percentage Flag   | Yes       |
| Percentage Value  | Yes       |
| Fixed Value       | Yes       |
| Active Status     | Yes       |

---

### Revenue Assurance Relevance

Priority:

Critical

Reason:

This module appears to contain the configuration rules that determine how customer statements are calculated.

Any incorrect configuration may directly impact:

* Revenue Share
* Owner Revenue
* Pango Revenue
* Statement Amounts
* Settlement Amounts

---

### Validation Objectives

| Validation                        | Status  |
| --------------------------------- | ------- |
| Statement Rule → Statement Output | Pending |
| Percentage Calculation Validation | Pending |
| Fixed Fee Validation              | Pending |
| Revenue Share Validation          | Pending |
| Settlement Calculation Validation | Pending |

---

### Key Observation

The platform separates:

Statement Generation
and
Statement Configuration

This indicates that statement calculations are governed by configurable business rules rather than hardcoded reporting logic.

This module may become one of the most important Revenue Assurance control points within the platform.

### Payments Ticket Module

Status:

Confirmed.

Description:

The Payments Ticket module manages parking citation and violation payments.

The module provides operational transaction records for ticket payments and their associated payment lifecycle.

---

### Ticket Payment Data Model

| Field           | Confirmed |
| --------------- | --------- |
| Ticket ID       | Yes       |
| City / Location | Yes       |
| Payment Date    | Yes       |
| Amount          | Yes       |
| Transaction Fee | Yes       |
| Payment Method  | Yes       |
| Payment Status  | Yes       |

---

### Payment Processing Data Model

| Field             | Confirmed |
| ----------------- | --------- |
| Payment ID        | Yes       |
| Module Type       | Yes       |
| Payment Type      | Yes       |
| Request Date      | Yes       |
| Final Status Date | Yes       |
| Status            | Yes       |

---

### Revenue Assurance Relevance

Priority:

High

Reason:

Violation payments represent an independent revenue stream with its own payment lifecycle and reconciliation requirements.

---

### Confirmed Violation Revenue Flow

Violation
→ Ticket Payment
→ Revenue
→ Statement
→ Processor
→ Bank
→ Accounting

Status:

Partially validated through backend analysis.


### Permit Validations Module

Status:

Confirmed.

Description:

The Permit Validations module records permit usage and validation events.

The module links permits to vehicle activity and permit holder information.

---

### Permit Validation Data Model

| Field           | Confirmed |
| --------------- | --------- |
| Account         | Yes       |
| First Name      | Yes       |
| Last Name       | Yes       |
| License Plate   | Yes       |
| Permit          | Yes       |
| Validation Date | Yes       |

---

### Revenue Assurance Relevance

Priority:

Medium

Reason:

The module does not directly generate revenue but provides operational evidence that active permits are being used.

---

### Validation Objectives

| Validation                | Status  |
| ------------------------- | ------- |
| Permit → Active Vehicle   | Pending |
| Permit → Validation Event | Pending |
| Permit → Revenue          | Pending |
| Permit → Statement        | Pending |

---

### Key Observation

Permit validations provide operational support for permit revenue and may be useful when investigating discrepancies between active permits and billed permits.

