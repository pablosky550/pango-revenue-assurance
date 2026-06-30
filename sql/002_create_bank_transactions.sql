USE PANGO_RA;

CREATE TABLE bank_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    source_system VARCHAR(30) NOT NULL,

    account_number VARCHAR(20) NOT NULL,

    transaction_date DATE NOT NULL,

    transaction_description TEXT NOT NULL,

    transaction_reference VARCHAR(100),

    transaction_type VARCHAR(50),

    debit_amount DECIMAL(12,2) DEFAULT 0.00,

    credit_amount DECIMAL(12,2) DEFAULT 0.00,

    running_balance DECIMAL(12,2) NOT NULL,

    currency CHAR(3) NOT NULL DEFAULT 'USD',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_account (account_number),
    INDEX idx_date (transaction_date),
    INDEX idx_type (transaction_type)
);

ALTER TABLE BANK_TRANSACTIONS CHANGE TRANSACTION_DESCRIPTION DESCRIPTION TEXT NOT NULL;
DESCRIBE bank_transactions;

