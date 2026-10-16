-- GLOBAL1TEL - database user creation (run as root BEFORE importing schema.sql)
--   mariadb -uroot -p < database/00-create-db-user.sql
-- Values must match config/.env  (DB_NAME / DB_USER / DB_PASS)

CREATE DATABASE IF NOT EXISTS `global1tel`
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'global1tel_user'@'localhost'
  IDENTIFIED BY 'global1tel_secure_pass_2026';
CREATE USER IF NOT EXISTS 'global1tel_user'@'127.0.0.1'
  IDENTIFIED BY 'global1tel_secure_pass_2026';

GRANT ALL PRIVILEGES ON `global1tel`.* TO 'global1tel_user'@'localhost';
GRANT ALL PRIVILEGES ON `global1tel`.* TO 'global1tel_user'@'127.0.0.1';
FLUSH PRIVILEGES;
