CREATE TABLE IF NOT EXISTS scale_surveys (
  id CHAR(36) PRIMARY KEY,
  code VARCHAR(64) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  cover_url TEXT NULL,
  survey_type VARCHAR(64) NULL,
  status ENUM('draft','published','stopped') NOT NULL DEFAULT 'draft',
  self_test_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  survey_json JSON NULL,
  version INT NOT NULL DEFAULT 1,
  created_by CHAR(36) NULL,
  published_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_scale_surveys_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_questions (
  id CHAR(36) PRIMARY KEY,
  survey_id CHAR(36) NOT NULL,
  question_type ENUM('radio','checkbox','text') NOT NULL,
  stem TEXT NOT NULL,
  media_url TEXT NULL,
  order_no INT NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_scale_questions_order (survey_id, order_no),
  CONSTRAINT fk_scale_questions_survey FOREIGN KEY (survey_id) REFERENCES scale_surveys(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_options (
  id CHAR(36) PRIMARY KEY,
  question_id CHAR(36) NOT NULL,
  option_no VARCHAR(16) NOT NULL,
  label TEXT NOT NULL,
  value DECIMAL(10,2) NOT NULL DEFAULT 0,
  order_no INT NOT NULL,
  media_url TEXT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_scale_options_order (question_id, order_no),
  CONSTRAINT fk_scale_options_question FOREIGN KEY (question_id) REFERENCES scale_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_dimensions (
  id CHAR(36) PRIMARY KEY,
  survey_id CHAR(36) NOT NULL,
  name VARCHAR(128) NOT NULL,
  code VARCHAR(64) NULL,
  num INT NOT NULL,
  raw_score_formula TEXT NOT NULL,
  standard_score_formula TEXT NULL,
  show_in_full_report BOOLEAN NOT NULL DEFAULT TRUE,
  show_in_user_report BOOLEAN NOT NULL DEFAULT TRUE,
  show_chart BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_scale_dimensions_num (survey_id, num),
  CONSTRAINT fk_scale_dimensions_survey FOREIGN KEY (survey_id) REFERENCES scale_surveys(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_result_definitions (
  id CHAR(36) PRIMARY KEY,
  dimension_id CHAR(36) NOT NULL,
  condition_expression TEXT NOT NULL,
  conclusion TEXT NULL,
  suggestion TEXT NULL,
  warning_level ENUM('none','low','middle','high') NOT NULL DEFAULT 'none',
  order_no INT NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_scale_result_definitions_dimension (dimension_id, order_no),
  CONSTRAINT fk_scale_result_definitions_dimension FOREIGN KEY (dimension_id) REFERENCES scale_dimensions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_distribution_plans (
  id CHAR(36) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  assessment_category ENUM('scale','neuropsych') NOT NULL DEFAULT 'scale',
  survey_ids JSON NULL,
  recipient_type ENUM('users','groups') NOT NULL DEFAULT 'users',
  recipient_scope JSON NULL,
  cover_url TEXT NULL,
  start_at DATETIME(3) NULL,
  end_at DATETIME(3) NULL,
  status ENUM('draft','active','stopped') NOT NULL DEFAULT 'active',
  created_by CHAR(36) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_scale_distribution_plans_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_distribution_records (
  id CHAR(36) PRIMARY KEY,
  plan_id CHAR(36) NOT NULL,
  survey_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  assessment_category ENUM('scale','neuropsych') NOT NULL DEFAULT 'scale',
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  calc_status ENUM('none','waiting','done','error') NOT NULL DEFAULT 'none',
  calc_error TEXT NULL,
  sent_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  answer_duration_sec INT NULL,
  answers_json JSON NULL,
  total_score DECIMAL(10,2) NULL,
  warning_level ENUM('none','low','middle','high') NOT NULL DEFAULT 'none',
  report JSON NULL,
  assessment_id CHAR(36) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_scale_records_plan_user_survey (plan_id, user_id, survey_id),
  KEY idx_scale_records_user_status (user_id, status, sent_at),
  KEY idx_scale_records_survey_completed (survey_id, completed_at),
  KEY idx_scale_records_calc_status (calc_status),
  KEY idx_scale_records_warning (warning_level),
  CONSTRAINT fk_scale_records_plan FOREIGN KEY (plan_id) REFERENCES scale_distribution_plans(id) ON DELETE CASCADE,
  CONSTRAINT fk_scale_records_survey FOREIGN KEY (survey_id) REFERENCES scale_surveys(id) ON DELETE CASCADE,
  CONSTRAINT fk_scale_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_scale_records_assessment FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_answers (
  id CHAR(36) PRIMARY KEY,
  record_id CHAR(36) NOT NULL,
  survey_id CHAR(36) NOT NULL,
  question_id CHAR(36) NOT NULL,
  question_type VARCHAR(32) NOT NULL,
  my_answer TEXT NULL,
  answer_text TEXT NULL,
  option_no VARCHAR(64) NULL,
  score DECIMAL(10,2) NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  KEY idx_scale_answers_record (record_id),
  CONSTRAINT fk_scale_answers_record FOREIGN KEY (record_id) REFERENCES scale_distribution_records(id) ON DELETE CASCADE,
  CONSTRAINT fk_scale_answers_survey FOREIGN KEY (survey_id) REFERENCES scale_surveys(id) ON DELETE CASCADE,
  CONSTRAINT fk_scale_answers_question FOREIGN KEY (question_id) REFERENCES scale_questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scale_record_dimensions (
  id CHAR(36) PRIMARY KEY,
  record_id CHAR(36) NOT NULL,
  dimension_id CHAR(36) NOT NULL,
  dimension_name VARCHAR(128) NOT NULL,
  dimension_code VARCHAR(64) NULL,
  raw_score DECIMAL(10,2) NULL,
  standard_score DECIMAL(10,2) NULL,
  conclusion TEXT NULL,
  suggestion TEXT NULL,
  warning_level ENUM('none','low','middle','high') NOT NULL DEFAULT 'none',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  KEY idx_scale_record_dimensions_record (record_id),
  CONSTRAINT fk_scale_record_dimensions_record FOREIGN KEY (record_id) REFERENCES scale_distribution_records(id) ON DELETE CASCADE,
  CONSTRAINT fk_scale_record_dimensions_dimension FOREIGN KEY (dimension_id) REFERENCES scale_dimensions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
