# Location Statement Structure

## Purpose

This document describes the common structure observed in location statements provided by Pango customers (cities, airports, universities, residential communities, and private operators).

The objective is to identify the business entities, revenue components, fee structures, and reconciliation points required for Revenue Assurance.

---

## Statement Components

| Component            | Description                            | RA Relevance |
| -------------------- | -------------------------------------- | ------------ |
| Location             | Customer / Property / Municipality     | High         |
| Period               | Reporting month                        | High         |
| Parking Sessions     | Number of parking transactions         | High         |
| Parking Extensions   | Session extensions (when available)    | Medium       |
| Zero Charge Sessions | Free parking sessions (when available) | Medium       |
| Parking Revenue      | Gross parking receipts                 | Critical     |
| Parking Refunds      | Refunded transactions                  | Critical     |
| Transaction Fee      | Pango processing fee                   | Critical     |
| Permit Revenue       | Permit-related revenue                 | High         |
| Permit Fees          | Permit processing fees                 | High         |
| Disputes             | Payment disputes / chargebacks         | High         |
| Dispute Fees         | Fees associated with disputes          | High         |
| Enforcement Revenue  | Enforcement-related activity           | Medium       |
| Enforcement Fees     | Enforcement service charges            | High         |
| Call Center Fees     | Customer support charges               | Medium       |
| Revenue Share        | Owner/Pango revenue split              | Critical     |
| Owner Revenue        | Revenue allocated to customer          | Critical     |
| Pango Revenue        | Revenue allocated to Pango             | Critical     |
| Net Receipts         | Final settlement amount                | Critical     |

---

## Revenue Models Observed

| Model                 | Description                                               |
| --------------------- | --------------------------------------------------------- |
| Fixed Transaction Fee | Percentage fee applied to parking revenue (typically 16%) |
| Revenue Share 70/30   | 70% Owner / 30% Pango                                     |
| Revenue Share 75/25   | 75% Owner / 25% Pango                                     |
| Per Session Fee       | Fixed fee charged per parking session                     |
| Enforcement Model     | Parking + enforcement service charges                     |
| Call Center Model     | Parking + customer support charges                        |

---

## Operational Entities Observed

| Entity Type                  | Examples                              |
| ---------------------------- | ------------------------------------- |
| City                         | Mount Vernon, Latrobe                 |
| Residential Community        | Henson Creek, Kings Gardens           |
| Apartment Complex            | Mosaic at Largo Station, LaSalle Park |
| University                   | La Salle University                   |
| Airport                      | Pending Validation                    |
| Corporate / Private Operator | Pending Validation                    |

---

## Core Revenue Assurance Metrics

| Metric              | Description                         |
| ------------------- | ----------------------------------- |
| Parking Sessions    | Number of billable parking events   |
| Gross Revenue       | Total parking revenue generated     |
| Refund Rate         | Refunds / Gross Revenue             |
| Revenue per Session | Gross Revenue / Sessions            |
| Fee Percentage      | Fees / Gross Revenue                |
| Owner Share         | Revenue allocated to location owner |
| Pango Share         | Revenue allocated to Pango          |
| Net Settlement      | Final amount payable                |

---

## Expected Reconciliation Path

Location
→ Parking Sessions
→ Gross Revenue
→ Fees / Adjustments
→ Net Settlement
→ Payment Processor
→ Bank
→ QuickBooks

---

## Revenue Assurance Validation Targets

| Validation                     | Status  |
| ------------------------------ | ------- |
| Sessions → Revenue             | Pending |
| Revenue → Processor Settlement | Pending |
| Processor Settlement → Bank    | Pending |
| Bank → QuickBooks              | Pending |
| Revenue Share Calculation      | Pending |
| Fee Calculation                | Pending |
| Refund Calculation             | Pending |
| Dispute Calculation            | Pending |

---

## Key Observation

Location statements provide the first direct link between operational activity (sessions, permits, tickets, enforcement) and financial outcomes (revenue, fees, settlements).

These statements are expected to become the primary source for validating end-to-end revenue flows.
