-- GLOBAL1TEL - Agent Range Request + Admin Profile Fields Upgrade
-- Safe to run on an existing database.
SET NAMES utf8mb4;

SET @sql := (SELECT IF(COUNT(*)=0,
  'ALTER TABLE user_profiles ADD COLUMN skype_id VARCHAR(100) NULL AFTER company',
  'SELECT 1')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='user_profiles' AND COLUMN_NAME='skype_id');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (SELECT IF(COUNT(*)=0,
  'ALTER TABLE user_profiles ADD COLUMN country VARCHAR(120) NULL AFTER skype_id',
  'SELECT 1')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='user_profiles' AND COLUMN_NAME='country');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (SELECT IF(COUNT(*)=0,
  'ALTER TABLE sms_ranges ADD COLUMN request_enabled TINYINT(1) NOT NULL DEFAULT 1 AFTER status',
  'SELECT 1')
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='sms_ranges' AND COLUMN_NAME='request_enabled');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE sms_ranges SET request_enabled=1 WHERE request_enabled IS NULL;
