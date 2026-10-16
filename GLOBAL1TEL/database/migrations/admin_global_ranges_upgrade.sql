-- GLOBAL1TEL: make Admin-created SMS ranges global for all Managers.
-- Safe compatibility migration: sms_ranges.manager_id remains NOT NULL and
-- points to an Admin account, while runtime Manager visibility is hierarchy based.

SET @g1t_admin_id := (
    SELECT id
    FROM users
    WHERE role='admin'
    ORDER BY CASE WHEN username='admin' THEN 0 ELSE 1 END, id
    LIMIT 1
);

UPDATE sms_ranges
SET manager_id=@g1t_admin_id
WHERE @g1t_admin_id IS NOT NULL
  AND manager_id<>@g1t_admin_id;
