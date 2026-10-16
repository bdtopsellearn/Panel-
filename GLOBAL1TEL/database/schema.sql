-- GLOBAL1TEL Database Schema
-- MySQL 5.7+ / MariaDB 10.3+

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Create Database
CREATE DATABASE IF NOT EXISTS `global1tel` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `global1tel`;

-- =====================================================
-- USERS TABLE (Admin, Managers, Agents, Clients)
-- =====================================================
CREATE TABLE `users` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(100) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) DEFAULT NULL,
    `role` ENUM('admin', 'manager', 'agent', 'client', 'test') NOT NULL DEFAULT 'client',
    `parent_id` INT UNSIGNED DEFAULT NULL COMMENT 'Hierarchy: manager->admin, agent->manager, client->agent',
    `status` ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    `api_token` VARCHAR(64) DEFAULT NULL,
    `last_login` DATETIME DEFAULT NULL,
    `login_ip` VARCHAR(45) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_api_token` (`api_token`),
    KEY `idx_parent` (`parent_id`),
    KEY `idx_role` (`role`),
    CONSTRAINT `fk_user_parent` FOREIGN KEY (`parent_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- USER PROFILES TABLE
-- =====================================================
CREATE TABLE `user_profiles` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `full_name` VARCHAR(255) DEFAULT NULL,
    `phone` VARCHAR(50) DEFAULT NULL,
    `address` TEXT DEFAULT NULL,
    `company` VARCHAR(255) DEFAULT NULL,
    `skype_id` VARCHAR(100) DEFAULT NULL,
    `country` VARCHAR(120) DEFAULT NULL,
    `timezone` VARCHAR(50) DEFAULT 'UTC',
    `avatar` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user` (`user_id`),
    CONSTRAINT `fk_profile_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- USER BALANCES TABLE
-- =====================================================
CREATE TABLE `user_balances` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `currency` ENUM('USD', 'EUR', 'GBP') NOT NULL DEFAULT 'USD',
    `balance` DECIMAL(15, 6) DEFAULT 0.000000,
    `held_balance` DECIMAL(15, 6) DEFAULT 0.000000 COMMENT 'Balance on hold',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_currency` (`user_id`, `currency`),
    CONSTRAINT `fk_balance_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SMS RANGES TABLE
-- =====================================================
CREATE TABLE `sms_ranges` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `manager_id` INT UNSIGNED NOT NULL,
    `range_name` VARCHAR(255) NOT NULL,
    `prefix` VARCHAR(20) NOT NULL,
    `currency` ENUM('USD', 'EUR', 'GBP') NOT NULL DEFAULT 'USD',
    `payout_1_1` DECIMAL(10, 6) DEFAULT NULL,
    `payout_7_1` DECIMAL(10, 6) DEFAULT NULL,
    `payout_7_7` DECIMAL(10, 6) DEFAULT NULL,
    `payout_30_45` DECIMAL(10, 6) DEFAULT NULL,
    `payout_1_1_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=1/1 payout term can be selected when requesting/assigning numbers',
    `payout_7_1_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=7/1 payout term can be selected when requesting/assigning numbers',
    `payout_7_7_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=7/7 payout term can be selected when requesting/assigning numbers',
    `payout_30_45_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=30/45 payout term can be selected when requesting/assigning numbers',
    `test_number` VARCHAR(50) DEFAULT NULL,
    `total_numbers` INT UNSIGNED DEFAULT 0,
    `available_numbers` INT UNSIGNED DEFAULT 0,
    `memo` TEXT DEFAULT NULL,
    `status` ENUM('active', 'inactive', 'exhausted') DEFAULT 'active',
    `request_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=Agents may submit number requests for this range',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_manager` (`manager_id`),
    KEY `idx_prefix` (`prefix`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_range_manager` FOREIGN KEY (`manager_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SMS NUMBERS TABLE
-- =====================================================
CREATE TABLE `sms_numbers` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `range_id` INT UNSIGNED NOT NULL,
    `number` VARCHAR(50) NOT NULL,
    `is_test` TINYINT(1) DEFAULT 0,
    `assigned_to` INT UNSIGNED DEFAULT NULL COMMENT 'User ID (agent or client)',
    `assigned_at` DATETIME DEFAULT NULL,
    `pay_term` VARCHAR(10) DEFAULT '1/1' COMMENT 'Payout term: 1/1, 7/1, 7/7, 30/45',
    `payout_rate` DECIMAL(10, 6) DEFAULT 0.000000,
    `status` ENUM('available', 'assigned', 'reserved') DEFAULT 'available',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_number` (`number`),
    KEY `idx_range` (`range_id`),
    KEY `idx_assigned` (`assigned_to`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_number_range` FOREIGN KEY (`range_id`) REFERENCES `sms_ranges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_number_user` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SMS CDR TABLE (Call Detail Records)
-- =====================================================
CREATE TABLE `sms_cdr` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `date_time` DATETIME NOT NULL,
    `range_id` INT UNSIGNED DEFAULT NULL,
    `number` VARCHAR(50) NOT NULL,
    `cli` VARCHAR(50) DEFAULT NULL COMMENT 'Caller ID',
    `user_id` INT UNSIGNED DEFAULT NULL COMMENT 'Agent or Client',
    `sms_count` INT UNSIGNED DEFAULT 1,
    `sms_type` ENUM('general', 'test') DEFAULT 'general',
    `message` TEXT DEFAULT NULL COMMENT 'Full SMS text, shown in CDR reports',
    `otp_detected` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 when inbound text looks like an OTP/verification message',
    `currency` ENUM('USD', 'EUR', 'GBP') DEFAULT 'USD',
    `my_payout` DECIMAL(10, 6) DEFAULT 0.000000 COMMENT 'Manager payout',
    `user_payout` DECIMAL(10, 6) DEFAULT 0.000000 COMMENT 'Assigned user payout',
    `agent_payout` DECIMAL(10, 6) DEFAULT 0.000000 COMMENT 'Agent override when assigned user is a client',
    `profit` DECIMAL(10, 6) DEFAULT 0.000000,
    `smpp_message_id` VARCHAR(50) DEFAULT NULL,
    `smpp_status` ENUM('delivered', 'failed', 'pending') DEFAULT 'delivered',
    `connector_id` VARCHAR(50) DEFAULT NULL,
    `processed_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_date` (`date_time`),
    KEY `idx_range` (`range_id`),
    KEY `idx_number` (`number`),
    KEY `idx_user` (`user_id`),
    KEY `idx_type` (`sms_type`),
    KEY `idx_otp_detected` (`otp_detected`),
    KEY `idx_smpp_message_id` (`smpp_message_id`),
    CONSTRAINT `fk_cdr_range` FOREIGN KEY (`range_id`) REFERENCES `sms_ranges` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_cdr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SMPP CONFIGURATION (Admin controlled)
-- =====================================================
CREATE TABLE `smpp_config` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `config_name` VARCHAR(50) NOT NULL DEFAULT 'primary',
    `inbound_host` VARCHAR(100) NOT NULL DEFAULT '0.0.0.0',
    `inbound_port` INT UNSIGNED NOT NULL DEFAULT 2775,
    `inbound_system_id` VARCHAR(50) NOT NULL,
    `inbound_password` VARCHAR(255) NOT NULL COMMENT 'Write-only password hash/reference',
    `status` ENUM('active', 'inactive', 'maintenance') NOT NULL DEFAULT 'inactive',
    `total_received` BIGINT UNSIGNED NOT NULL DEFAULT 0,
    `last_received_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by` INT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_smpp_config_status` (`status`),
    KEY `idx_smpp_config_created_by` (`created_by`),
    CONSTRAINT `fk_smpp_config_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- RAW SMPP CDR
-- =====================================================
CREATE TABLE `smpp_cdr` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `message_id` VARCHAR(100) NOT NULL,
    `source_addr` VARCHAR(50) NOT NULL,
    `destination_addr` VARCHAR(50) NOT NULL,
    `short_message` TEXT,
    `message_status` ENUM('delivered', 'failed', 'pending') NOT NULL DEFAULT 'delivered',
    `submit_date` DATETIME NOT NULL,
    `done_date` DATETIME DEFAULT NULL,
    `cdr_id` BIGINT UNSIGNED DEFAULT NULL,
    `connector_id` VARCHAR(50) DEFAULT NULL,
    `route_id` VARCHAR(50) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_smpp_cdr_destination` (`destination_addr`),
    KEY `idx_smpp_cdr_source` (`source_addr`),
    KEY `idx_smpp_cdr_submit_date` (`submit_date`),
    KEY `idx_smpp_cdr_message_id` (`message_id`),
    KEY `idx_smpp_cdr_cdr_id` (`cdr_id`),
    CONSTRAINT `fk_smpp_cdr_main` FOREIGN KEY (`cdr_id`) REFERENCES `sms_cdr` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- SMPP SUPPLIER USERS
-- =====================================================
CREATE TABLE `smpp_users` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `supplier_name` VARCHAR(100) DEFAULT NULL,
    `supplier_contact` VARCHAR(100) DEFAULT NULL,
    `bind_type` ENUM('TX', 'RX', 'TR') NOT NULL DEFAULT 'TR',
    `max_connections` INT UNSIGNED NOT NULL DEFAULT 10,
    `allowed_ranges` TEXT DEFAULT NULL,
    `status` ENUM('active', 'suspended', 'disabled') NOT NULL DEFAULT 'active',
    `total_messages` BIGINT UNSIGNED NOT NULL DEFAULT 0,
    `last_connected_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_by` INT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_smpp_users_username` (`username`),
    KEY `idx_smpp_users_created_by` (`created_by`),
    CONSTRAINT `fk_smpp_users_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- NUMBER REQUESTS TABLE
-- =====================================================
CREATE TABLE `number_requests` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `range_id` INT UNSIGNED NOT NULL,
    `quantity` INT UNSIGNED NOT NULL,
    `pay_term` VARCHAR(20) DEFAULT '1/1',
    `status` ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    `notes` TEXT DEFAULT NULL,
    `processed_by` INT UNSIGNED DEFAULT NULL,
    `processed_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    KEY `idx_range` (`range_id`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_request_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_request_range` FOREIGN KEY (`range_id`) REFERENCES `sms_ranges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_request_processor` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- NEWS TABLE
-- =====================================================
CREATE TABLE `news` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `author_id` INT UNSIGNED NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `target_role` ENUM('all', 'agent', 'client') DEFAULT 'all',
    `status` ENUM('draft', 'published', 'archived') DEFAULT 'published',
    `published_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_author` (`author_id`),
    KEY `idx_status` (`status`),
    KEY `idx_target` (`target_role`),
    CONSTRAINT `fk_news_author` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- PAYMENT REQUESTS TABLE
-- =====================================================
CREATE TABLE `payment_requests` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `currency` ENUM('USD', 'EUR', 'GBP') NOT NULL,
    `amount` DECIMAL(15, 6) NOT NULL,
    `method` VARCHAR(50) DEFAULT NULL,
    `details` TEXT DEFAULT NULL,
    `status` ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    `processed_by` INT UNSIGNED DEFAULT NULL,
    `processed_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_payment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payment_processor` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CREDIT NOTES TABLE
-- =====================================================
CREATE TABLE `credit_notes` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `currency` ENUM('USD', 'EUR', 'GBP') NOT NULL,
    `amount` DECIMAL(15, 6) NOT NULL,
    `type` ENUM('credit', 'debit') NOT NULL,
    `reference` VARCHAR(255) DEFAULT NULL,
    `notes` TEXT DEFAULT NULL,
    `created_by` INT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    CONSTRAINT `fk_credit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_credit_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- USER ACTIVITY LOG TABLE
-- =====================================================
CREATE TABLE `user_activity` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED DEFAULT NULL,
    `action` VARCHAR(100) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `user_agent` VARCHAR(500) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    KEY `idx_action` (`action`),
    KEY `idx_date` (`created_at`),
    CONSTRAINT `fk_activity_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- NOTIFICATIONS TABLE
-- =====================================================
CREATE TABLE `notifications` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `message` TEXT NOT NULL,
    `type` ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
    `is_read` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    KEY `idx_read` (`is_read`),
    CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- API CONFIGURATION TABLE (Jasmin Gateway)
-- =====================================================
CREATE TABLE `api_config` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `manager_id` INT UNSIGNED NOT NULL,
    `config_key` VARCHAR(100) NOT NULL,
    `config_value` TEXT DEFAULT NULL,
    `is_encrypted` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_manager_key` (`manager_id`, `config_key`),
    CONSTRAINT `fk_config_manager` FOREIGN KEY (`manager_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- GLOBAL SYSTEM SETTINGS (Admin)
-- =====================================================
CREATE TABLE `system_settings` (
    `setting_key` VARCHAR(100) NOT NULL,
    `setting_value` TEXT DEFAULT NULL,
    `setting_type` ENUM('string', 'number', 'boolean') NOT NULL DEFAULT 'string',
    `updated_by` INT UNSIGNED DEFAULT NULL,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`setting_key`),
    KEY `idx_settings_updated_by` (`updated_by`),
    CONSTRAINT `fk_settings_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `system_settings` (`setting_key`, `setting_value`, `setting_type`) VALUES
('site_name', 'GLOBAL1TEL', 'string'),
('minimum_withdrawal_usd', '10', 'number'),
('minimum_withdrawal_eur', '10', 'number'),
('minimum_withdrawal_gbp', '10', 'number'),
('payment_requests_enabled', '1', 'boolean'),
('maintenance_mode', '0', 'boolean'),
('default_page_size', '25', 'number'),
('support_note', '', 'string');

-- =====================================================
-- LOGIN ATTEMPTS TABLE (Rate Limiting)
-- =====================================================
CREATE TABLE `login_attempts` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(100) NOT NULL,
    `ip_address` VARCHAR(45) NOT NULL,
    `attempts` INT DEFAULT 1,
    `locked_until` DATETIME DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_username` (`username`),
    KEY `idx_ip` (`ip_address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CAPTCHA SESSION TABLE
-- =====================================================
CREATE TABLE `captcha_sessions` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `session_id` VARCHAR(64) NOT NULL,
    `captcha_answer` INT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `expires_at` DATETIME NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_session` (`session_id`),
    KEY `idx_expires` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- INSERT DEFAULT MANAGER ACCOUNT
-- =====================================================
INSERT INTO `users` (`username`, `password`, `email`, `role`, `status`, `api_token`) VALUES
('GLOBAL1TEL', SHA2(CONCAT('mbc_sms_secure_salt_2024', 'GLOBAL1TEL'), 256), 'manager@global1tel.com', 'manager', 'active', SHA2(CONCAT('mbc_sms_secure_salt_2024', 'manager_token_', NOW()), 256));

INSERT INTO `user_profiles` (`user_id`, `full_name`, `phone`, `timezone`) VALUES
(1, 'GLOBAL1TEL Manager', '+1234567890', 'UTC');

INSERT INTO `user_balances` (`user_id`, `currency`, `balance`) VALUES
(1, 'USD', 1000.000000),
(1, 'EUR', 500.000000),
(1, 'GBP', 250.000000);

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Sample Agent
INSERT INTO `users` (`username`, `password`, `email`, `role`, `parent_id`, `status`, `api_token`) VALUES
('agent1', SHA2(CONCAT('mbc_sms_secure_salt_2024', 'agent1'), 256), 'agent1@global1tel.com', 'agent', 1, 'active', SHA2(CONCAT('mbc_sms_secure_salt_2024', 'agent_token_', NOW()), 256));

INSERT INTO `user_profiles` (`user_id`, `full_name`, `phone`, `timezone`) VALUES
(2, 'Test Agent', '+1987654321', 'UTC');

INSERT INTO `user_balances` (`user_id`, `currency`, `balance`) VALUES
(2, 'USD', 100.000000);

-- Sample Client
INSERT INTO `users` (`username`, `password`, `email`, `role`, `parent_id`, `status`, `api_token`) VALUES
('client1', SHA2(CONCAT('mbc_sms_secure_salt_2024', 'client1'), 256), 'client1@global1tel.com', 'client', 2, 'active', SHA2(CONCAT('mbc_sms_secure_salt_2024', 'client_token_', NOW()), 256));

INSERT INTO `user_profiles` (`user_id`, `full_name`, `phone`, `timezone`) VALUES
(3, 'Test Client', '+1122334455', 'UTC');

INSERT INTO `user_balances` (`user_id`, `currency`, `balance`) VALUES
(3, 'USD', 50.000000);

-- Sample SMS Range
INSERT INTO `sms_ranges` (`manager_id`, `range_name`, `prefix`, `currency`, `payout_1_1`, `payout_7_1`, `payout_7_7`, `payout_30_45`, `test_number`, `total_numbers`, `available_numbers`, `memo`, `status`) VALUES
(1, 'UK Premium', '447', 'USD', 0.0500, 0.0400, NULL, NULL, '4471234567', 100, 95, 'UK Mobile Numbers', 'active');

-- Sample Numbers
INSERT INTO `sms_numbers` (`range_id`, `number`, `is_test`, `status`) VALUES
(1, '4471234567', 1, 'available'),
(1, '4471234568', 0, 'available'),
(1, '4471234569', 0, 'available');

-- Sample News
INSERT INTO `news` (`author_id`, `title`, `content`, `target_role`, `status`) VALUES
(1, 'Welcome to GLOBAL1TEL', 'Welcome to the GLOBAL1TEL platform. We are excited to have you on board!', 'all', 'published');


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

SET FOREIGN_KEY_CHECKS = 1;

-- Bank accounts for payment withdrawals
CREATE TABLE IF NOT EXISTS `bank_accounts` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT UNSIGNED NOT NULL,
    `bank_name` VARCHAR(100) NOT NULL,
    `account_title` VARCHAR(150) NOT NULL,
    `account_number` VARCHAR(100) NOT NULL,
    `currency` ENUM('USD', 'EUR', 'GBP') DEFAULT 'USD',
    `account_type` VARCHAR(30) DEFAULT 'bank',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    CONSTRAINT `fk_bank_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
