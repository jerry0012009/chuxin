ALTER TABLE scale_distribution_records
  DROP FOREIGN KEY fk_scale_records_plan;

ALTER TABLE scale_distribution_records
  DROP INDEX uk_scale_records_plan_user_survey;

ALTER TABLE scale_distribution_records
  MODIFY plan_id CHAR(36) NULL;

ALTER TABLE scale_distribution_records
  ADD COLUMN source_type ENUM('assigned','self') NOT NULL DEFAULT 'assigned' AFTER assessment_category;

ALTER TABLE scale_distribution_records
  ADD KEY idx_scale_records_source (source_type, created_at);

ALTER TABLE scale_distribution_records
  ADD CONSTRAINT fk_scale_records_plan FOREIGN KEY (plan_id) REFERENCES scale_distribution_plans(id) ON DELETE CASCADE;
