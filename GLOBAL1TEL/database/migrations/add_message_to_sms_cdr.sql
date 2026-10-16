-- Adds the full SMS text column so CDR Stats/Reports pages can display the
-- actual message instead of just a count. Safe to re-run.
ALTER TABLE `sms_cdr`
    ADD COLUMN IF NOT EXISTS `message` TEXT DEFAULT NULL
    COMMENT 'Full SMS text, shown in CDR reports' AFTER `sms_type`;
