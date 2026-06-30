/*
===============================================================================
PANGO REVENUE ASSURANCE CONTROLS
Phase 1
===============================================================================

Purpose

This file contains the first set of automated Revenue Assurance controls.

Each control validates a specific point within the revenue lifecycle.

Revenue Flow

Customer
    ↓
Backend
    ↓
Payment Processor
    ↓
Bank
    ↓
Accounting

===============================================================================
*/

-- ============================================================================
-- RA001
-- Daily PayPal Settlement Amount
--
-- Objective:
-- Validate the amount received from PayPal each day.
--
-- Risk:
-- Missing settlements.
-- ============================================================================

SELECT
    transaction_date,
    COUNT(*) AS settlements,
    SUM(credit_amount) AS total_received
FROM bank_transactions
WHERE transaction_type='PAYPAL_SETTLEMENT'
GROUP BY transaction_date
ORDER BY transaction_date;

-- ============================================================================
-- RA002
-- Daily PayPal Processing
--
-- Objective:
-- Measure daily payment processing activity.
-- ============================================================================

SELECT
    DATE(transaction_datetime) AS processing_day,
    COUNT(*) AS transactions,
    SUM(gross_amount) AS gross_amount,
    SUM(fee_amount) AS processor_fees,
    SUM(net_amount) AS net_amount
FROM payment_transactions
WHERE raw_type='PreApproved Payment Bill User Payment'
GROUP BY DATE(transaction_datetime)
ORDER BY processing_day;

-- ============================================================================
-- RA003
-- Refund Ratio
--
-- Objective:
-- Detect abnormal refund behaviour.
-- ============================================================================

SELECT
    DATE(transaction_datetime) AS refund_day,
    COUNT(*) AS refunds,
    SUM(gross_amount) AS refunded_amount
FROM payment_transactions
WHERE raw_type='Payment Refund'
GROUP BY DATE(transaction_datetime)
ORDER BY refund_day;

-- ============================================================================
-- RA004
-- Processor Fee Percentage
--
-- Objective:
-- Validate processor fee consistency.
-- ============================================================================

SELECT
    ROUND(
        SUM(ABS(fee_amount))
        /
        SUM(gross_amount)
        *100,
        2
    ) AS fee_percentage
FROM payment_transactions
WHERE raw_type='PreApproved Payment Bill User Payment';

-- ============================================================================
-- RA005
-- Largest PayPal Settlements
--
-- Objective:
-- Detect unusually large settlements.
-- ============================================================================

SELECT
    transaction_date,
    description,
    credit_amount
FROM bank_transactions
WHERE transaction_type='PAYPAL_SETTLEMENT'
ORDER BY credit_amount DESC
LIMIT 20;

-- ============================================================================
-- RA006
-- Largest Customer Payments
-- ============================================================================

SELECT
    transaction_datetime,
    gross_amount,
    payer
FROM payment_transactions
ORDER BY gross_amount DESC
LIMIT 20;

-- ============================================================================
-- RA007
-- Settlement Frequency
-- ============================================================================

SELECT
    transaction_date,
    COUNT(*) AS settlements
FROM bank_transactions
GROUP BY transaction_date
ORDER BY transaction_date;

-- ============================================================================
-- RA008
-- Daily Average Customer Payment
-- ============================================================================

SELECT
    DATE(transaction_datetime) AS payment_day,
    ROUND(
        AVG(gross_amount),
        2
    ) AS average_ticket
FROM payment_transactions
WHERE raw_type='PreApproved Payment Bill User Payment'
GROUP BY DATE(transaction_datetime)
ORDER BY payment_day;

