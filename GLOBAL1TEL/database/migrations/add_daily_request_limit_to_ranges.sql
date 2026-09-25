-- Migration: Per-range DAILY self-request quantity limit for Agents
-- Lets Admin cap how many numbers (total quantity, not request count) a
-- single Agent may self-request from a given range PER CALENDAR DAY via the
-- "Request Numbers" button on the SMS Ranges page. The quota resets
-- automatically every day because usage is tracked per (range, agent, date).
-- NULL or 0 = unlimited, so existing ranges keep today's behaviour until
-- Admin sets a limit.
-- MySQL 5.7+ / MariaDB 10.3+

ALTER TABLE sms_ranges
ADD COLUMN IF NOT EXISTS max_numbers_per_agent_daily INT UNSIGNED DEFAULT NULL
  COMMENT 'Max total numbers one Agent may self-request from this range per calendar day. NULL/0 = unlimited.'
  AFTER max_requests_per_agent;

CREATE TABLE IF NOT EXISTS sms_range_agent_daily_requests (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    range_id INT UNSIGNED NOT NULL,
    agent_id INT UNSIGNED NOT NULL,
    request_date DATE NOT NULL,
    qty_requested INT UNSIGNED NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_range_agent_date (range_id, agent_id, request_date),
    KEY idx_agent (agent_id),
    CONSTRAINT fk_radr_range FOREIGN KEY (range_id) REFERENCES sms_ranges(id) ON DELETE CASCADE,
    CONSTRAINT fk_radr_agent FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
