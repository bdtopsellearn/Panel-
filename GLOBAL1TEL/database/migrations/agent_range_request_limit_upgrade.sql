-- Migration: Per-Agent request-count limit per SMS range
-- Lets Admin cap how many separate "Request Numbers" submissions a single
-- Agent may make against a given range (e.g. only 2 requests total, ever).
-- This is independent of Quantity (1-200 numbers per request) and independent
-- of the existing request_enabled on/off switch.
-- NULL or 0 = unlimited, so existing ranges keep today's behaviour until
-- Admin sets a limit.
-- MySQL 5.7+ / MariaDB 10.3+

ALTER TABLE sms_ranges
ADD COLUMN IF NOT EXISTS max_requests_per_agent INT UNSIGNED DEFAULT NULL
  COMMENT 'Max number of separate request submissions one Agent may make for this range. NULL/0 = unlimited.'
  AFTER request_enabled;

-- One row per (range, agent) pair, counting how many times that Agent has
-- successfully submitted a number request against that range.
CREATE TABLE IF NOT EXISTS sms_range_agent_requests (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    range_id INT UNSIGNED NOT NULL,
    agent_id INT UNSIGNED NOT NULL,
    request_count INT UNSIGNED NOT NULL DEFAULT 0,
    last_requested_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_range_agent (range_id, agent_id),
    KEY idx_agent (agent_id),
    CONSTRAINT fk_rar_range FOREIGN KEY (range_id) REFERENCES sms_ranges(id) ON DELETE CASCADE,
    CONSTRAINT fk_rar_agent FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
