/*
===========================================================
REVENUE ASSURANCE QUERIES
Project: Pango Revenue Assurance
Phase: 1
===========================================================
*/

-- =========================================================
-- Q001
-- Daily Bank Activity by Transaction Type
-- =========================================================

SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(credit_amount) AS total_credits,
    SUM(debit_amount) AS total_debits
FROM bank_transactions
GROUP BY transaction_type
ORDER BY total_credits DESC;

-- =========================================================
-- Q002
-- Daily PayPal Settlements
-- =========================================================

SELECT
    transaction_date,
    COUNT(*) AS transfers,
    SUM(credit_amount) AS total_received
FROM bank_transactions
WHERE transaction_type = 'PAYPAL_SETTLEMENT'
GROUP BY transaction_date
ORDER BY transaction_date;

-- =========================================================
-- Q003
-- Daily Braintree Settlements
-- =========================================================

SELECT
    transaction_date,
    COUNT(*) AS transfers,
    SUM(credit_amount) AS total_received
FROM bank_transactions
WHERE transaction_type = 'BRAINTREE_SETTLEMENT'
GROUP BY transaction_date
ORDER BY transaction_date;

-- =========================================================
-- Q004
-- Daily PayPal Processing
-- =========================================================

SELECT
    DATE(transaction_datetime) AS processing_date,
    COUNT(*) AS transactions,
    SUM(gross_amount) AS gross_amount,
    SUM(fee_amount) AS processor_fees,
    SUM(net_amount) AS net_amount
FROM payment_transactions
WHERE raw_type = 'PreApproved Payment Bill User Payment'
GROUP BY DATE(transaction_datetime)
ORDER BY processing_date;

-- =========================================================
-- Q005
-- PayPal Refunds
-- =========================================================

SELECT
    DATE(transaction_datetime) AS refund_date,
    COUNT(*) AS refunds,
    SUM(gross_amount) AS refunded_amount
FROM payment_transactions
WHERE raw_type = 'Payment Refund'
GROUP BY DATE(transaction_datetime)
ORDER BY refund_date;

-- =========================================================
-- Q006
-- PayPal Disputes
-- =========================================================

SELECT
    raw_type,
    COUNT(*) AS transactions
FROM payment_transactions
WHERE raw_type LIKE '%Dispute%'
   OR raw_type LIKE '%Chargeback%'
GROUP BY raw_type;

