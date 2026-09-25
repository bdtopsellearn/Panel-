-- GLOBAL1TEL: repair the default Test account so it can log in.
-- Username: test | Password: test | Role: test
-- Uses the same hashing algorithm/salt as the application defaults.

UPDATE users
SET password = SHA2(CONCAT('mbc_sms_secure_salt_2024','test'),256),
    role = 'test',
    status = 'active'
WHERE username = 'test';

INSERT INTO user_profiles (user_id, full_name, timezone)
SELECT u.id, 'Test Account', 'UTC'
FROM users u
LEFT JOIN user_profiles p ON p.user_id = u.id
WHERE u.username='test' AND u.role='test' AND p.user_id IS NULL;

INSERT INTO user_balances (user_id,currency,balance)
SELECT u.id,'USD',0 FROM users u
LEFT JOIN user_balances b ON b.user_id=u.id AND b.currency='USD'
WHERE u.username='test' AND u.role='test' AND b.id IS NULL;

INSERT INTO user_balances (user_id,currency,balance)
SELECT u.id,'EUR',0 FROM users u
LEFT JOIN user_balances b ON b.user_id=u.id AND b.currency='EUR'
WHERE u.username='test' AND u.role='test' AND b.id IS NULL;

INSERT INTO user_balances (user_id,currency,balance)
SELECT u.id,'GBP',0 FROM users u
LEFT JOIN user_balances b ON b.user_id=u.id AND b.currency='GBP'
WHERE u.username='test' AND u.role='test' AND b.id IS NULL;
