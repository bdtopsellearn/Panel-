-- GLOBAL1TEL Admin SMPP + News for Agents upgrade
-- MySQL 5.7+ / MariaDB 10.3+
-- Back up the database before applying this migration.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Admin-owned SMPP connection profiles.
CREATE TABLE IF NOT EXISTS `smpp_config` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `config_name` VARCHAR(50) NOT NULL DEFAULT 'primary',
    `inbound_host` VARCHAR(100) NOT NULL DEFAULT '0.0.0.0',
    `inbound_port` INT UNSIGNED NOT NULL DEFAULT 2775,
    `inbound_system_id` VARCHAR(50) NOT NULL,
    `inbound_password` VARCHAR(255) NOT NULL COMMENT 'Write-only password hash/reference; never returned by Admin API',
    `status` ENUM('active','inactive','maintenance') NOT NULL DEFAULT 'inactive',
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

-- Raw gateway CDR. Existing production installations keep their current table/data.
CREATE TABLE IF NOT EXISTS `smpp_cdr` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `message_id` VARCHAR(100) NOT NULL,
    `source_addr` VARCHAR(50) NOT NULL,
    `destination_addr` VARCHAR(50) NOT NULL,
    `short_message` TEXT,
    `message_status` ENUM('delivered','failed','pending') NOT NULL DEFAULT 'delivered',
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

-- Supplier credentials table retained for SMPP integrations. Admin panel does not expose hashes.
CREATE TABLE IF NOT EXISTS `smpp_users` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `supplier_name` VARCHAR(100) DEFAULT NULL,
    `supplier_contact` VARCHAR(100) DEFAULT NULL,
    `bind_type` ENUM('TX','RX','TR') NOT NULL DEFAULT 'TR',
    `max_connections` INT UNSIGNED NOT NULL DEFAULT 10,
    `allowed_ranges` TEXT DEFAULT NULL,
    `status` ENUM('active','suspended','disabled') NOT NULL DEFAULT 'active',
    `total_messages` BIGINT UNSIGNED NOT NULL DEFAULT 0,
    `last_connected_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_by` INT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_smpp_users_username` (`username`),
    KEY `idx_smpp_users_created_by` (`created_by`),
    CONSTRAINT `fk_smpp_users_created_by` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- The existing `news` table already supports target_role='agent'.
-- Admin-created Agent announcements use that existing path so Agent dashboards
-- immediately display published announcements without an extra table.

SET FOREIGN_KEY_CHECKS = 1;
