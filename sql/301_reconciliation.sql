/*
===============================================================================
PANGO REVENUE ASSURANCE
RECONCILIATION CONTROLS
Phase 1
===============================================================================

Objective

Validate the flow of money between:

Customer
    ↓
PayPal
    ↓
FirstBank
    ↓
Accounting (Future)

===============================================================================
*/

-- ============================================================================
-- RA101
-- Daily PayPal Net Processing
--
-- Objective:
-- Calculate the daily net amount processed by PayPal.
--
-- Risk:
-- Incorrect processor settlements.
-- ============================================================================

SELECT
    DATE(transaction_datetime) AS processing_day,
    COUNT(*) AS transactions,
    ROUND(SUM(gross_amount),2) AS gross_amount,
    ROUND(SUM(ABS(fee_amount)),2) AS processor_fees,
    ROUND(SUM(net_amount),2) AS net_amount
FROM payment_transactions
WHERE raw_type='PreApproved Payment Bill User Payment'
GROUP BY DATE(transaction_datetime)
ORDER BY processing_day;

-- ============================================================================
-- RA102
-- Daily Bank PayPal Settlements
--
-- Objective:
-- Calculate the daily PayPal deposits received in FirstBank.
--
-- Risk:
-- Missing processor settlements.
-- ============================================================================

SELECT
    transaction_date,
    COUNT(*) AS settlements,
    ROUND(SUM(credit_amount),2) AS settlement_amount
FROM bank_transactions
WHERE transaction_type='PAYPAL_SETTLEMENT'
GROUP BY transaction_date
ORDER BY transaction_date;

-- ============================================================================
-- RA103
-- Daily Reconciliation
--
-- Objective:
-- Compare PayPal processing against FirstBank settlements.
--
-- Current Status:
-- Prototype.
-- ============================================================================

SELECT
    p.processing_day,

    p.net_amount AS paypal_net,

    b.settlement_amount AS bank_received,

    ROUND(
        p.net_amount - b.settlement_amount,
        2
    ) AS variance

FROM (

    SELECT

        DATE(transaction_datetime) AS processing_day,

        SUM(net_amount) AS net_amount

    FROM payment_transactions

    WHERE raw_type='PreApproved Payment Bill User Payment'

    GROUP BY DATE(transaction_datetime)

) p

LEFT JOIN (

    SELECT

        transaction_date,

        SUM(credit_amount) AS settlement_amount

    FROM bank_transactions

    WHERE transaction_type='PAYPAL_SETTLEMENT'

    GROUP BY transaction_date

) b

ON p.processing_day=b.transaction_date

ORDER BY p.processing_day;

-- ============================================================================
-- RA104
-- Missing Settlement Days
-- ============================================================================

SELECT *

FROM (

    SELECT

        DATE(transaction_datetime) AS processing_day,

        SUM(net_amount) AS net_amount

    FROM payment_transactions

    WHERE raw_type='PreApproved Payment Bill User Payment'

    GROUP BY DATE(transaction_datetime)

) p

LEFT JOIN (

    SELECT DISTINCT

        transaction_date

    FROM bank_transactions

    WHERE transaction_type='PAYPAL_SETTLEMENT'

) b

ON p.processing_day=b.transaction_date

WHERE b.transaction_date IS NULL;

