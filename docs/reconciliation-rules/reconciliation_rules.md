# Rule 001

Every Braintree funding deposit must be traceable to:

Braintree
↓
Bank Account 2092

Status:
Pending validation

# Rule 002

Every transfer:

2092 → 2084

Must correspond to payroll funding

Status:
Validated

# Rule 003

Every transfer:

7922 → 1523

Must have documented treasury purpose

Status:
Validated

# Rule 004

Every customer statement must be traceable to:

Operational Activity
↓
Revenue Calculation
↓
Generated Statement

Status:
Partially Validated

Evidence:
Statements are generated directly from the Pango platform.

---

# Rule 005

Every mobile payment transaction must be traceable to:

Parking Session
↓
PreApproved Payment Bill User Payment
↓
PayPal Settlement
↓
PayPal Withdrawal
↓
Bank Deposit

Status:
Partially Validated

Evidence:
Backend mobile payment activity and PayPal transaction records identified.

---

# Rule 006

Every permit transaction must be traceable to:

Permit
↓
Permit Charge
↓
Permit Revenue
↓
Statement
↓
Payment Processor
↓
Bank Deposit

Status:
Partially Validated

Evidence:
Permit Management and BI Permit modules identified.

---

# Rule 007

Every reservation transaction must be traceable to:

Reservation
↓
Reservation Charge
↓
Statement
↓
Payment Processor
↓
Bank Deposit

Status:
Partially Validated

Evidence:
Reservation Management module identified.

---

# Rule 008

Every violation payment must be traceable to:

Violation
↓
Ticket Payment
↓
Revenue
↓
Statement
↓
Payment Processor
↓
Bank Deposit

Status:
Partially Validated

Evidence:
Payments Ticket and BI Pay Violations modules identified.

---

# Rule 009

Every refund recorded in the backend must be traceable to:

Original Transaction
↓
Refund
↓
Payment Processor Refund
↓
Settlement Adjustment

Status:
Pending Validation

Evidence:
Refund module identified in backend.
Refund transactions identified in PayPal exports.

---

# Rule 010

Every dispute recorded in the backend must be traceable to:

Original Transaction
↓
Dispute
↓
Chargeback / Dispute Hold
↓
Settlement Adjustment

Status:
Pending Validation

Evidence:
Dispute module identified in backend.
Chargeback and dispute transactions identified in PayPal exports.

---

# Rule 011

Every statement calculation must be traceable to:

Statement Configuration Rule
↓
Revenue Calculation
↓
Statement Output

Status:
Partially Validated

Evidence:
Statements Manager module identified.
