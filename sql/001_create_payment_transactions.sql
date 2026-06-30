USE PANGO_RA;
SHOW TABLES;

CREATE TABLE payment_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    source_system VARCHAR(20) NOT NULL,

    transaction_id VARCHAR(100) NOT NULL,
    reference_transaction_id VARCHAR(100),

    transaction_type VARCHAR(100) NOT NULL,
    raw_type VARCHAR(255),

    transaction_status VARCHAR(50),

    transaction_datetime DATETIME NOT NULL,

    currency CHAR(3) NOT NULL,

    gross_amount DECIMAL(12,2) NOT NULL,
    fee_amount DECIMAL(12,2) NOT NULL,
    net_amount DECIMAL(12,2) NOT NULL,

    payer VARCHAR(255),
    payee VARCHAR(255),

    balance DECIMAL(12,2),

    balance_impact VARCHAR(20),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_datetime (transaction_datetime),
    INDEX idx_type (transaction_type),
    INDEX idx_transaction (transaction_id),
    INDEX idx_source (source_system)
);