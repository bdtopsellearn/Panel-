-- GLOBAL1TEL: Test Role Upgrade
-- Adds the standalone "test" role without changing existing users.
-- MySQL 5.7+ / MariaDB 10.3+
-- BACK UP THE DATABASE BEFORE RUNNING MIGRATIONS.

SET @g1t_role_sql := (
  SELECT IF(
    EXISTS(
      SELECT 1 FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA=DATABASE()
        AND TABLE_NAME='users'
        AND COLUMN_NAME='role'
        AND COLUMN_TYPE LIKE '%''test''%'
    ),
    'SELECT 1',
    'ALTER TABLE users MODIFY COLUMN role ENUM(''admin'',''manager'',''agent'',''client'',''test'') NOT NULL DEFAULT ''client'''
  )
);
PREPARE g1t_role_stmt FROM @g1t_role_sql;
EXECUTE g1t_role_stmt;
DEALLOCATE PREPARE g1t_role_stmt;

-- Create the default Test account only if it does not already exist.
INSERT INTO users (username,password,email,role,parent_id,status,api_token)
SELECT 'test',
       SHA2(CONCAT('mbc_sms_secure_salt_2024','test'),256),
       'test@global1tel.local',
       'test',
       NULL,
       'active',
       SHA2(CONCAT('g1t_test_',UUID(),NOW()),256)
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='test');

INSERT INTO user_profiles (user_id,full_name,timezone)
SELECT u.id,'Test Account','UTC'
FROM users u
LEFT JOIN user_profiles p ON p.user_id=u.id
WHERE u.username='test' AND u.role='test' AND p.user_id IS NULL;

INSERT INTO user_balances (user_id,currency,balance)
SELECT u.id,'USD',0
FROM users u
LEFT JOIN user_balances b ON b.user_id=u.id AND b.currency='USD'
WHERE u.username='test' AND u.role='test' AND b.id IS NULL;

INSERT INTO user_balances (user_id,currency,balance)
SELECT u.id,'EUR',0
FROM users u
LEFT JOIN user_balances b ON b.user_id=u.id AND b.currency='EUR'
WHERE u.username='test' AND u.role='test' AND b.id IS NULL;

INSERT INTO user_balances (user_id,currency,balance)
SELECT u.id,'GBP',0
FROM users u
LEFT JOIN user_balances b ON b.user_id=u.id AND b.currency='GBP'
WHERE u.username='test' AND u.role='test' AND b.id IS NULL;
