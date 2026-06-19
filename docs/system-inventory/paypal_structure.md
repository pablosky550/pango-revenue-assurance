# PayPal Structure

## Purpose

This document describes the PayPal payment processing layer used by Pango and identifies the transaction types, settlement mechanisms, fees, refunds, disputes, and reconciliation points relevant for Revenue Assurance.

---

## PayPal Role in Revenue Flow

Backend Activity
→ PayPal Transaction
→ PayPal Settlement
→ Bank Deposit
→ Accounting

Status:

Partially validated.

---

## Transaction Types Observed

| Transaction Type                            | Observed | Notes                       |
| ------------------------------------------- | -------- | --------------------------- |
| PreApproved Payment Bill User Payment       | Yes      | Primary transaction type    |
| General Withdrawal                          | Yes      | Settlement transfer to bank |
| Payment Refund                              | Yes      | Refund processing           |
| Hold on Balance for Dispute Investigation   | Yes      | Dispute workflow            |
| Cancellation of Hold for Dispute Resolution | Yes      | Dispute resolution workflow |
| Chargeback                                  | Yes      | Chargeback processing       |
| Chargeback Fee                              | Yes      | Chargeback fees             |
| Chargeback Reversal                         | Yes      | Chargeback recovery         |

---

## Financial Components

| Component      | Observed |
| -------------- | -------- |
| Gross Payments | Yes      |
| Processor Fees | Yes      |
| Net Payments   | Yes      |
| Withdrawals    | Yes      |
| Refunds        | Yes      |
| Disputes       | Yes      |
| Chargebacks    | Yes      |

---

## Revenue Assurance Relevance

Priority:

Critical

Reason:

PayPal represents one of the primary payment processing layers between operational revenue and bank deposits.

---

## Validation Objectives

| Validation                            | Status  |
| ------------------------------------- | ------- |
| Backend Revenue → PayPal Transactions | Pending |
| PayPal Fees → Processor Fees          | Pending |
| PayPal Refunds → Backend Refunds      | Pending |
| PayPal Disputes → Backend Disputes    | Pending |
| PayPal Withdrawals → Bank Deposits    | Pending |
| PayPal Activity → Accounting          | Pending |

---

## Key Observation

The majority of PayPal activity is generated through pre-approved recurring payment transactions.

PayPal appears to function as a settlement layer between operational activity and bank deposits.
