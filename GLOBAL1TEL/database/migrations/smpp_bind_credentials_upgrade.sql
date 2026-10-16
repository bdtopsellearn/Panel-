-- =====================================================
-- GLOBAL1TEL - SMPP bind credential upgrade
-- =====================================================
-- Why this exists:
--   The original panel stored SMPP supplier accounts in `smpp_users` with a
--   one-way password hash. An SMPP bind_transceiver PDU carries the password
--   in plaintext, so a one-way hash can NEVER be matched against it - which
--   means no carrier could ever bind and every inbound OTP was lost.
--
--   This migration adds the columns the live SMPP engine needs:
--     bind_password     reversible (base64) copy of the bind password
--     system_id         the SMPP system_id (defaults to `username`)
--     interconnect_type 'smpp-server' = carrier connects to us (default)
--                       'smpp-client' = we connect out to the carrier
--     host / port       only used for 'smpp-client' accounts
--
--   `password_hash` is left untouched so nothing that reads it breaks.
--   Safe to run more than once.
-- =====================================================

-- system_id ------------------------------------------------------------
SET @sql := IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'smpp_users'
       AND COLUMN_NAME = 'system_id') = 0,
  'ALTER TABLE `smpp_users` ADD COLUMN `system_id` VARCHAR(50) NULL AFTER `username`',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

-- bind_password --------------------------------------------------------
SET @sql := IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'smpp_users'
       AND COLUMN_NAME = 'bind_password') = 0,
  'ALTER TABLE `smpp_users` ADD COLUMN `bind_password` VARCHAR(255) NULL AFTER `password_hash`',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

-- interconnect_type ----------------------------------------------------
SET @sql := IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'smpp_users'
       AND COLUMN_NAME = 'interconnect_type') = 0,
  'ALTER TABLE `smpp_users` ADD COLUMN `interconnect_type` VARCHAR(20) NOT NULL DEFAULT ''smpp-server'' AFTER `bind_type`',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

-- host -----------------------------------------------------------------
SET @sql := IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'smpp_users'
       AND COLUMN_NAME = 'host') = 0,
  'ALTER TABLE `smpp_users` ADD COLUMN `host` VARCHAR(190) NULL AFTER `interconnect_type`',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

-- port -----------------------------------------------------------------
SET @sql := IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'smpp_users'
       AND COLUMN_NAME = 'port') = 0,
  'ALTER TABLE `smpp_users` ADD COLUMN `port` INT UNSIGNED NULL AFTER `host`',
  'SELECT 1');
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;

-- backfill system_id from username for existing rows --------------------
UPDATE `smpp_users`
   SET `system_id` = `username`
 WHERE `system_id` IS NULL OR `system_id` = '';
