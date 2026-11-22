INSERT INTO doctor_verification_codes (
  id,
  code,
  is_permanent,
  is_used,
  used_by,
  used_at,
  created_by,
  created_at,
  notes
)
VALUES (
  '65d259f5-890a-4587-98af-cda9a23cb0cd',
  '2026',
  TRUE,
  FALSE,
  NULL,
  NULL,
  NULL,
  CURRENT_TIMESTAMP(3),
  'Default permanent doctor verification code for local development'
)
ON DUPLICATE KEY UPDATE
  notes = VALUES(notes);
