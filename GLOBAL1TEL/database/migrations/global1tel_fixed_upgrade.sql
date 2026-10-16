-- GLOBAL1TEL upgrade for an existing global1tel database.
-- Safe to run more than once on MariaDB versions that support ADD COLUMN IF NOT EXISTS.

ALTER TABLE sms_numbers
    ADD COLUMN IF NOT EXISTS pay_term VARCHAR(10) DEFAULT '1/1',
    ADD COLUMN IF NOT EXISTS payout_rate DECIMAL(10,6) DEFAULT 0;

ALTER TABLE sms_cdr
    ADD COLUMN IF NOT EXISTS agent_payout DECIMAL(10,6) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS smpp_message_id VARCHAR(50) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS smpp_status ENUM('delivered','failed','pending') DEFAULT 'delivered',
    ADD COLUMN IF NOT EXISTS connector_id VARCHAR(50) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS processed_at DATETIME DEFAULT NULL;

UPDATE sms_numbers
SET pay_term = '1/1'
WHERE pay_term IS NULL OR pay_term = '';
