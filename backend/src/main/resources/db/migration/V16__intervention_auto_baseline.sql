ALTER TABLE intervention_publish_batches
  MODIFY batch_type ENUM('manual','auto_after_screening','auto_baseline') NOT NULL DEFAULT 'manual';
