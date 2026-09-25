-- GLOBAL1TEL Admin Panel upgrade
-- MySQL 5.7+ / MariaDB 10.3+
-- Back up the database before applying this migration.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Add Admin and separate Test roles. Existing manager/agent/client rows are preserved.
ALTER TABLE users
  MODIFY COLUMN role ENUM('admin','manager','agent','client','test') NOT NULL DEFAULT 'client';

-- Add privacy-preserving OTP classification when it is not already present.
SET @sql = (
  SELECT IF(
    EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='sms_cdr' AND COLUMN_NAME='otp_detected'),
    'SELECT 1',
    'ALTER TABLE sms_cdr ADD COLUMN otp_detected TINYINT(1) NOT NULL DEFAULT 0 AFTER sms_type'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='sms_cdr' AND INDEX_NAME='idx_otp_detected'),
    'SELECT 1',
    'ALTER TABLE sms_cdr ADD INDEX idx_otp_detected (otp_detected)'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Global system controls managed from the Admin panel.
CREATE TABLE IF NOT EXISTS system_settings (
  `setting_key` VARCHAR(100) NOT NULL,
  `setting_value` TEXT DEFAULT NULL,
  `setting_type` ENUM('string','number','boolean') NOT NULL DEFAULT 'string',
  `updated_by` INT UNSIGNED DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`setting_key`),
  KEY `idx_settings_updated_by` (`updated_by`),
  CONSTRAINT `fk_settings_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO system_settings (setting_key, setting_value, setting_type) VALUES
  ('site_name', 'GLOBAL1TEL', 'string'),
  ('minimum_withdrawal_usd', '10', 'number'),
  ('minimum_withdrawal_eur', '10', 'number'),
  ('minimum_withdrawal_gbp', '10', 'number'),
  ('payment_requests_enabled', '1', 'boolean'),
  ('maintenance_mode', '0', 'boolean'),
  ('default_page_size', '25', 'number'),
  ('support_note', '', 'string')
ON DUPLICATE KEY UPDATE setting_key = VALUES(setting_key);


-- =====================================================
-- DEFAULT ADMIN ACCOUNT
-- Login path: /adminlogin
-- Username: admin
-- Password: G1TAdmin@2026!
-- IMPORTANT: change this password immediately after first login.
-- =====================================================
INSERT INTO `users` (`username`,`password`,`email`,`role`,`parent_id`,`status`,`api_token`)
SELECT 'admin', SHA2(CONCAT('mbc_sms_secure_salt_2024','G1TAdmin@2026!'),256), 'admin@global1tel.local', 'admin', NULL, 'active', SHA2(CONCAT('g1t_admin_',UUID(),NOW()),256)
WHERE NOT EXISTS (SELECT 1 FROM `users` WHERE `username`='admin');

INSERT INTO `user_profiles` (`user_id`,`full_name`,`timezone`)
SELECT u.id,'System Administrator','UTC'
FROM `users` u
LEFT JOIN `user_profiles` p ON p.user_id=u.id
WHERE u.username='admin' AND u.role='admin' AND p.user_id IS NULL;

INSERT INTO `user_balances` (`user_id`,`currency`,`balance`)
SELECT u.id,'USD',0 FROM `users` u LEFT JOIN `user_balances` b ON b.user_id=u.id AND b.currency='USD'
WHERE u.username='admin' AND u.role='admin' AND b.id IS NULL;
INSERT INTO `user_balances` (`user_id`,`currency`,`balance`)
SELECT u.id,'EUR',0 FROM `users` u LEFT JOIN `user_balances` b ON b.user_id=u.id AND b.currency='EUR'
WHERE u.username='admin' AND u.role='admin' AND b.id IS NULL;
INSERT INTO `user_balances` (`user_id`,`currency`,`balance`)
SELECT u.id,'GBP',0 FROM `users` u LEFT JOIN `user_balances` b ON b.user_id=u.id AND b.currency='GBP'
WHERE u.username='admin' AND u.role='admin' AND b.id IS NULL;

-- Attach any legacy root Managers to the default Admin hierarchy.
UPDATE `users` m JOIN `users` a ON a.username='admin' AND a.role='admin'
SET m.parent_id=a.id
WHERE m.role='manager' AND m.parent_id IS NULL;


-- Admin owns the technical FK for every SMS range; runtime Manager access is
-- global for available inventory and hierarchy-based for assigned numbers/CDRs.
UPDATE `sms_ranges` r
JOIN `users` a ON a.username='admin' AND a.role='admin'
SET r.manager_id=a.id;

SET FOREIGN_KEY_CHECKS = 1;
