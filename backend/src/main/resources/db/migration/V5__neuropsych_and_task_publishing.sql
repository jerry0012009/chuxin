CREATE TABLE IF NOT EXISTS neuropsych_tests (
  id CHAR(36) PRIMARY KEY,
  code VARCHAR(64) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  dimension VARCHAR(128) NULL,
  clinical_meaning TEXT NULL,
  estimated_minutes INT NULL,
  source_path VARCHAR(255) NULL,
  runner_type VARCHAR(32) NOT NULL DEFAULT 'iframe',
  status ENUM('active','stopped') NOT NULL DEFAULT 'active',
  self_test_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  config_json JSON NULL,
  metric_schema_json JSON NULL,
  scoring_version INT NOT NULL DEFAULT 1,
  created_by CHAR(36) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_neuropsych_tests_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_publish_batches (
  id CHAR(36) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  status ENUM('draft','active','stopped') NOT NULL DEFAULT 'draft',
  start_at DATETIME(3) NULL,
  end_at DATETIME(3) NULL,
  recipient_type ENUM('users','groups') NOT NULL DEFAULT 'users',
  recipient_scope JSON NULL,
  created_by CHAR(36) NULL,
  published_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_assessment_publish_batches_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_publish_items (
  id CHAR(36) PRIMARY KEY,
  batch_id CHAR(36) NOT NULL,
  item_type ENUM('scale','neuropsych','dialogue_scale','voice','expression','multimodal_baseline') NOT NULL,
  target_id CHAR(36) NULL,
  title VARCHAR(255) NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  order_no INT NOT NULL DEFAULT 0,
  config_json JSON NULL,
  status ENUM('enabled','disabled') NOT NULL DEFAULT 'enabled',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  KEY idx_assessment_publish_items_batch (batch_id, order_no),
  CONSTRAINT fk_assessment_publish_items_batch FOREIGN KEY (batch_id) REFERENCES assessment_publish_batches(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_publish_assignees (
  id CHAR(36) PRIMARY KEY,
  batch_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_assessment_publish_assignees_batch_user (batch_id, user_id),
  KEY idx_assessment_publish_assignees_user_status (user_id, status, created_at),
  CONSTRAINT fk_assessment_publish_assignees_batch FOREIGN KEY (batch_id) REFERENCES assessment_publish_batches(id) ON DELETE CASCADE,
  CONSTRAINT fk_assessment_publish_assignees_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS assessment_publish_item_records (
  id CHAR(36) PRIMARY KEY,
  assignee_id CHAR(36) NOT NULL,
  batch_id CHAR(36) NOT NULL,
  item_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  item_type ENUM('scale','neuropsych','dialogue_scale','voice','expression','multimodal_baseline') NOT NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled','unsupported') NOT NULL DEFAULT 'pending',
  result_ref_table VARCHAR(64) NULL,
  result_ref_id CHAR(36) NULL,
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_assessment_publish_item_records_user_status (user_id, status, created_at),
  KEY idx_assessment_publish_item_records_result (result_ref_table, result_ref_id),
  CONSTRAINT fk_assessment_publish_item_records_assignee FOREIGN KEY (assignee_id) REFERENCES assessment_publish_assignees(id) ON DELETE CASCADE,
  CONSTRAINT fk_assessment_publish_item_records_item FOREIGN KEY (item_id) REFERENCES assessment_publish_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_assessment_publish_item_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS neuropsych_records (
  id CHAR(36) PRIMARY KEY,
  test_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  source_type ENUM('assigned','self') NOT NULL DEFAULT 'assigned',
  publish_item_record_id CHAR(36) NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  calc_status ENUM('none','waiting','done','error') NOT NULL DEFAULT 'none',
  calc_error TEXT NULL,
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  duration_ms INT NULL,
  raw_data_json JSON NULL,
  metrics_json JSON NULL,
  report JSON NULL,
  warning_level ENUM('none','low','middle','high') NOT NULL DEFAULT 'none',
  assessment_id CHAR(36) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_neuropsych_records_user_status (user_id, status, created_at),
  KEY idx_neuropsych_records_test_completed (test_id, completed_at),
  KEY idx_neuropsych_records_warning (warning_level),
  CONSTRAINT fk_neuropsych_records_test FOREIGN KEY (test_id) REFERENCES neuropsych_tests(id),
  CONSTRAINT fk_neuropsych_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_neuropsych_records_publish_item FOREIGN KEY (publish_item_record_id) REFERENCES assessment_publish_item_records(id) ON DELETE SET NULL,
  CONSTRAINT fk_neuropsych_records_assessment FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO neuropsych_tests (
  id, code, title, description, dimension, clinical_meaning, estimated_minutes, source_path,
  runner_type, status, self_test_enabled, config_json, metric_schema_json, scoring_version
) VALUES
  (
    '90000000-0000-0000-0000-000000000001',
    'go-nogo',
    'Go-NoGo 反应抑制任务',
    '通过 Go 与 NoGo 刺激反应评估反应抑制、冲动控制和注意维持。',
    '反应抑制能力、冲动控制',
    '可辅助 ADHD、冲动控制问题、物质依赖和强迫相关症状的执行功能评估。',
    10,
    'neuropsych/expfactory/go-nogo/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","outputs":["go_rt_mean","go_accuracy","nogo_false_alarm_rate","d_prime","criterion_c"]}' AS JSON),
    CAST('{"primary":["goRtMean","goAccuracy","nogoFalseAlarmRate","dPrime","criterionC"]}' AS JSON),
    1
  ),
  (
    '90000000-0000-0000-0000-000000000002',
    'columbia-card-task-hot',
    '哥伦比亚卡片任务（热版）',
    '在时间压力和即时反馈中评估风险决策、冲动控制和热认知表现。',
    '风险决策、冲动控制、热认知',
    '可辅助风险评估、冲动行为预测和执行功能评估。',
    25,
    'neuropsych/expfactory/columbia-card-task-hot/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","rounds":28,"outputs":["avg_cards","loss_rate","total_score","decision_rt_mean"]}' AS JSON),
    CAST('{"primary":["avgCardsPerRound","lossHitRate","totalScore","decisionRtMean","riskAdjustment"]}' AS JSON),
    1
  ),
  (
    '90000000-0000-0000-0000-000000000003',
    'discount-titrate',
    '延迟折扣任务',
    '通过即时较小奖励和延迟较大奖励的选择评估延迟折扣、自我控制和跨期决策。',
    '延迟折扣率、自我控制、跨期选择',
    '可辅助成瘾行为风险、自我控制能力和经济决策倾向分析。',
    5,
    'neuropsych/expfactory/discount-titrate/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","outputs":["discount_k","immediate_choice_rate","delayed_choice_rate","consistency"]}' AS JSON),
    CAST('{"primary":["discountK","immediateChoiceRate","delayedChoiceRate","consistency","decisionRtMean"]}' AS JSON),
    1
  )
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  dimension = VALUES(dimension),
  clinical_meaning = VALUES(clinical_meaning),
  estimated_minutes = VALUES(estimated_minutes),
  source_path = VALUES(source_path),
  config_json = VALUES(config_json),
  metric_schema_json = VALUES(metric_schema_json),
  updated_at = CURRENT_TIMESTAMP(3);
