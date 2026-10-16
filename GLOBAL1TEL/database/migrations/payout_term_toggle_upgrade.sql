-- Migration: Per-term ON/OFF toggles for SMS range payouts
-- Lets Admin keep a payout value saved but switch any single term
-- (1/1, 7/1, 7/7, 30/45) off without clearing its rate. Disabled terms
-- are hidden from Agent/Manager "add number" (request/assign) flows.
-- MySQL 5.7+ / MariaDB 10.3+

ALTER TABLE sms_ranges
ADD COLUMN IF NOT EXISTS payout_1_1_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=1/1 payout term can be selected when requesting/assigning numbers' AFTER payout_30_45,
ADD COLUMN IF NOT EXISTS payout_7_1_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=7/1 payout term can be selected when requesting/assigning numbers' AFTER payout_1_1_enabled,
ADD COLUMN IF NOT EXISTS payout_7_7_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=7/7 payout term can be selected when requesting/assigning numbers' AFTER payout_7_1_enabled,
ADD COLUMN IF NOT EXISTS payout_30_45_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=30/45 payout term can be selected when requesting/assigning numbers' AFTER payout_7_7_enabled;

-- Existing ranges keep every term enabled by default so behaviour is unchanged until Admin turns one off.
UPDATE sms_ranges
SET payout_1_1_enabled = 1, payout_7_1_enabled = 1, payout_7_7_enabled = 1, payout_30_45_enabled = 1
WHERE payout_1_1_enabled IS NULL OR payout_7_1_enabled IS NULL OR payout_7_7_enabled IS NULL OR payout_30_45_enabled IS NULL;
