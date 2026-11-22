ALTER TABLE assessment_publish_batches
  ADD COLUMN batch_type ENUM('manual','auto_default') NOT NULL DEFAULT 'manual' AFTER id,
  ADD COLUMN template_code VARCHAR(64) NULL AFTER batch_type,
  ADD COLUMN auto_assign_enabled BOOLEAN NOT NULL DEFAULT FALSE AFTER template_code;

ALTER TABLE assessment_publish_item_records
  ADD COLUMN report JSON NULL AFTER result_ref_id,
  ADD COLUMN warning_level ENUM('none','low','middle','high') NOT NULL DEFAULT 'none' AFTER report;

CREATE TABLE IF NOT EXISTS assessment_task_module_records (
  id CHAR(36) PRIMARY KEY,
  item_record_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  module_type ENUM('dialogue_scale','voice','expression','multimodal_baseline') NOT NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  raw_data_json JSON NULL,
  metrics_json JSON NULL,
  report JSON NULL,
  warning_level ENUM('none','low','middle','high') NOT NULL DEFAULT 'none',
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_task_module_records_item (item_record_id),
  KEY idx_task_module_records_user_type (user_id, module_type, created_at),
  CONSTRAINT fk_task_module_records_item FOREIGN KEY (item_record_id) REFERENCES assessment_publish_item_records(id) ON DELETE CASCADE,
  CONSTRAINT fk_task_module_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO assessment_publish_batches (
  id, batch_type, template_code, auto_assign_enabled, title, description, status, recipient_type, recipient_scope, published_at, created_at, updated_at
) VALUES (
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
  'auto_default',
  'default_forensic_risk_screening',
  TRUE,
  '职务犯罪风险与心理状态初筛',
  '新用户注册后自动分配的默认五段式测评任务，用于评估风险决策、冲动控制与心理状态。',
  'active',
  'users',
  CAST('{"auto":true}' AS JSON),
  CURRENT_TIMESTAMP(3),
  CURRENT_TIMESTAMP(3),
  CURRENT_TIMESTAMP(3)
) ON DUPLICATE KEY UPDATE
  batch_type = VALUES(batch_type),
  template_code = VALUES(template_code),
  auto_assign_enabled = VALUES(auto_assign_enabled),
  title = VALUES(title),
  description = VALUES(description),
  status = VALUES(status),
  recipient_scope = VALUES(recipient_scope),
  updated_at = CURRENT_TIMESTAMP(3);

INSERT INTO assessment_publish_items (
  id, batch_id, item_type, target_id, title, required, order_no, config_json, status, created_at
)
SELECT 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1411',
       'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
       'scale',
       s.id,
       s.title,
       TRUE,
       1,
       CAST('{"default":true,"reason":"risk_impulse"}' AS JSON),
       'enabled',
       CURRENT_TIMESTAMP(3)
FROM scale_surveys s
WHERE s.code = 'huaxinyun-118'
LIMIT 1
ON DUPLICATE KEY UPDATE target_id = VALUES(target_id), title = VALUES(title), status = VALUES(status);

INSERT INTO assessment_publish_items (
  id, batch_id, item_type, target_id, title, required, order_no, config_json, status, created_at
)
SELECT 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1412',
       'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
       'scale',
       s.id,
       s.title,
       TRUE,
       2,
       CAST('{"default":true,"reason":"mental_state"}' AS JSON),
       'enabled',
       CURRENT_TIMESTAMP(3)
FROM scale_surveys s
WHERE s.code = 'huaxinyun-107'
LIMIT 1
ON DUPLICATE KEY UPDATE target_id = VALUES(target_id), title = VALUES(title), status = VALUES(status);

INSERT INTO assessment_publish_items (
  id, batch_id, item_type, target_id, title, required, order_no, config_json, status, created_at
)
SELECT 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1413',
       'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
       'neuropsych',
       t.id,
       t.title,
       TRUE,
       3,
       CAST('{"default":true,"reason":"risk_decision"}' AS JSON),
       'enabled',
       CURRENT_TIMESTAMP(3)
FROM neuropsych_tests t
WHERE t.code = 'columbia-card-task-hot-demo'
LIMIT 1
ON DUPLICATE KEY UPDATE target_id = VALUES(target_id), title = VALUES(title), status = VALUES(status);

INSERT INTO assessment_publish_items (
  id, batch_id, item_type, target_id, title, required, order_no, config_json, status, created_at
)
SELECT 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1414',
       'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
       'neuropsych',
       t.id,
       t.title,
       TRUE,
       4,
       CAST('{"default":true,"reason":"delay_discounting"}' AS JSON),
       'enabled',
       CURRENT_TIMESTAMP(3)
FROM neuropsych_tests t
WHERE t.code = 'discount-titrate-demo'
LIMIT 1
ON DUPLICATE KEY UPDATE target_id = VALUES(target_id), title = VALUES(title), status = VALUES(status);

INSERT INTO assessment_publish_items (
  id, batch_id, item_type, target_id, title, required, order_no, config_json, status, created_at
) VALUES
  (
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1415',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
    'dialogue_scale',
    NULL,
    '对话式心理健康评估',
    TRUE,
    5,
    CAST('{"default":true,"prompts":["请描述最近一周的压力、冲动或情绪变化。","当遇到诱惑或冲突时，你通常如何控制自己的行为？"]}' AS JSON),
    'enabled',
    CURRENT_TIMESTAMP(3)
  ),
  (
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1416',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
    'voice',
    NULL,
    '语音识别',
    TRUE,
    6,
    CAST('{"default":true,"durationSeconds":10}' AS JSON),
    'enabled',
    CURRENT_TIMESTAMP(3)
  ),
  (
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1417',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1401',
    'expression',
    NULL,
    '表情评估',
    TRUE,
    7,
    CAST('{"default":true,"durationSeconds":5}' AS JSON),
    'enabled',
    CURRENT_TIMESTAMP(3)
  )
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  required = VALUES(required),
  order_no = VALUES(order_no),
  config_json = VALUES(config_json),
  status = VALUES(status);
