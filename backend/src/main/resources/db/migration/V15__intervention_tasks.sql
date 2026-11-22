CREATE TABLE IF NOT EXISTS intervention_materials (
  id CHAR(36) PRIMARY KEY,
  code VARCHAR(96) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  category ENUM('meditation','mood','game','knowledge','brain_intervention') NOT NULL,
  subtype VARCHAR(64) NULL,
  target_ref_table VARCHAR(64) NULL,
  target_ref_id CHAR(36) NULL,
  route_path VARCHAR(255) NOT NULL,
  duration_sec INT NOT NULL DEFAULT 10,
  completion_mode ENUM('countdown','diary_once','media_end') NOT NULL DEFAULT 'countdown',
  tags JSON NULL,
  config_json JSON NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_plan_templates (
  id CHAR(36) PRIMARY KEY,
  code VARCHAR(96) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  risk_level ENUM('low','middle','high') NOT NULL,
  description TEXT NULL,
  duration_days INT NOT NULL DEFAULT 7,
  daily_required_count INT NOT NULL DEFAULT 1,
  auto_assign_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  status ENUM('draft','active','stopped') NOT NULL DEFAULT 'active',
  created_by CHAR(36) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_templates_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_plan_template_items (
  id CHAR(36) PRIMARY KEY,
  template_id CHAR(36) NOT NULL,
  material_id CHAR(36) NOT NULL,
  title VARCHAR(255) NOT NULL,
  frequency_type ENUM('daily','weekly','once','plan_total') NOT NULL DEFAULT 'daily',
  required_count INT NOT NULL DEFAULT 1,
  duration_sec INT NOT NULL DEFAULT 10,
  order_no INT NOT NULL DEFAULT 1,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  config_json JSON NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_template_items_template FOREIGN KEY (template_id) REFERENCES intervention_plan_templates(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_template_items_material FOREIGN KEY (material_id) REFERENCES intervention_materials(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_publish_batches (
  id CHAR(36) PRIMARY KEY,
  batch_type ENUM('manual','auto_after_screening') NOT NULL DEFAULT 'manual',
  template_id CHAR(36) NULL,
  source_assessment_id CHAR(36) NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  risk_level ENUM('low','middle','high') NULL,
  duration_days INT NOT NULL DEFAULT 7,
  daily_required_count INT NOT NULL DEFAULT 1,
  status ENUM('draft','active','stopped','completed') NOT NULL DEFAULT 'draft',
  start_date DATE NULL,
  end_date DATE NULL,
  recipient_type ENUM('users','groups') NOT NULL DEFAULT 'users',
  recipient_scope JSON NULL,
  created_by CHAR(36) NULL,
  published_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_intervention_batches_status (status, created_at),
  CONSTRAINT fk_intervention_batches_template FOREIGN KEY (template_id) REFERENCES intervention_plan_templates(id) ON DELETE SET NULL,
  CONSTRAINT fk_intervention_batches_source_assessment FOREIGN KEY (source_assessment_id) REFERENCES assessments(id) ON DELETE SET NULL,
  CONSTRAINT fk_intervention_batches_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_publish_items (
  id CHAR(36) PRIMARY KEY,
  batch_id CHAR(36) NOT NULL,
  material_id CHAR(36) NOT NULL,
  item_type ENUM('meditation','mood','game','knowledge','brain_intervention') NOT NULL,
  subtype VARCHAR(64) NULL,
  title VARCHAR(255) NOT NULL,
  route_path VARCHAR(255) NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  frequency_type ENUM('daily','weekly','once','plan_total') NOT NULL DEFAULT 'daily',
  required_count INT NOT NULL DEFAULT 1,
  duration_sec INT NOT NULL DEFAULT 10,
  completion_mode ENUM('countdown','diary_once','media_end') NOT NULL DEFAULT 'countdown',
  order_no INT NOT NULL DEFAULT 1,
  config_json JSON NULL,
  status ENUM('enabled','disabled') NOT NULL DEFAULT 'enabled',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_items_batch FOREIGN KEY (batch_id) REFERENCES intervention_publish_batches(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_items_material FOREIGN KEY (material_id) REFERENCES intervention_materials(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_publish_assignees (
  id CHAR(36) PRIMARY KEY,
  batch_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  source_assessment_id CHAR(36) NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  completed_days INT NOT NULL DEFAULT 0,
  total_completed_count INT NOT NULL DEFAULT 0,
  last_completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_intervention_assignees_batch_user (batch_id, user_id),
  UNIQUE KEY uk_intervention_assignees_source_report (user_id, source_assessment_id),
  KEY idx_intervention_assignees_user_status (user_id, status, start_date),
  CONSTRAINT fk_intervention_assignees_batch FOREIGN KEY (batch_id) REFERENCES intervention_publish_batches(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_assignees_source_assessment FOREIGN KEY (source_assessment_id) REFERENCES assessments(id) ON DELETE SET NULL,
  CONSTRAINT fk_intervention_assignees_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_item_records (
  id CHAR(36) PRIMARY KEY,
  assignee_id CHAR(36) NOT NULL,
  batch_id CHAR(36) NOT NULL,
  item_id CHAR(36) NOT NULL,
  material_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  plan_date DATE NOT NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  source_ref_table VARCHAR(64) NULL,
  source_ref_id CHAR(36) NULL,
  duration_seconds INT NULL,
  completion_note TEXT NULL,
  summary_json JSON NULL,
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_intervention_item_day (assignee_id, item_id, plan_date),
  KEY idx_intervention_item_records_user_date (user_id, plan_date, status),
  KEY idx_intervention_item_records_assignee_date (assignee_id, plan_date),
  CONSTRAINT fk_intervention_records_assignee FOREIGN KEY (assignee_id) REFERENCES intervention_publish_assignees(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_records_item FOREIGN KEY (item_id) REFERENCES intervention_publish_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_records_material FOREIGN KEY (material_id) REFERENCES intervention_materials(id) ON DELETE RESTRICT,
  CONSTRAINT fk_intervention_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS intervention_daily_summaries (
  id CHAR(36) PRIMARY KEY,
  assignee_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  summary_date DATE NOT NULL,
  completed_count INT NOT NULL DEFAULT 0,
  required_count INT NOT NULL DEFAULT 0,
  mood_level VARCHAR(32) NULL,
  summary_text TEXT NULL,
  details_json JSON NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_intervention_daily_summary (assignee_id, summary_date),
  CONSTRAINT fk_intervention_daily_assignee FOREIGN KEY (assignee_id) REFERENCES intervention_publish_assignees(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_daily_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO intervention_materials (
  id, code, title, description, category, subtype, target_ref_table, target_ref_id, route_path, duration_sec, completion_mode, tags, config_json, is_active
) VALUES
  ('10000000-0000-0000-0000-000000000001', 'mood-diary', '心情日记', '记录当天情绪、触发因素和主要想法。', 'mood', 'diary', NULL, NULL, '/record', 0, 'diary_once', JSON_ARRAY('情绪记录','每日'), JSON_OBJECT(), TRUE),
  ('10000000-0000-0000-0000-000000000002', 'breathing-relax', '焦虑缓解呼吸法', '短时呼吸练习，帮助降低紧张感。', 'meditation', 'audio', 'healing_contents', 'dddd4444-4444-4444-4444-444444444444', '/healing?tab=meditation&track=m1', 10, 'countdown', JSON_ARRAY('呼吸','放松'), JSON_OBJECT('track','m1'), TRUE),
  ('10000000-0000-0000-0000-000000000003', 'sleep-relax', '睡前放松引导', '睡前放松练习，适合晚间稳定情绪。', 'meditation', 'audio', 'healing_contents', 'eeee5555-5555-5555-5555-555555555555', '/healing?tab=meditation&track=m2', 10, 'countdown', JSON_ARRAY('睡眠','放松'), JSON_OBJECT('track','m2'), TRUE),
  ('10000000-0000-0000-0000-000000000004', 'body-scan', '身体扫描冥想', '通过身体扫描建立觉察，缓解紧绷。', 'meditation', 'audio', 'healing_contents', 'ffff6666-6666-6666-6666-666666666666', '/healing?tab=meditation&track=m3', 10, 'countdown', JSON_ARRAY('正念','减压'), JSON_OBJECT('track','m3'), TRUE),
  ('10000000-0000-0000-0000-000000000005', 'focus-training', '专注力训练', '轻量专注训练，帮助形成稳定任务节奏。', 'meditation', 'audio', 'healing_contents', '9999aaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '/healing?tab=meditation&track=m4', 10, 'countdown', JSON_ARRAY('专注','训练'), JSON_OBJECT('track','m4'), TRUE),
  ('10000000-0000-0000-0000-000000000006', 'knowledge-anxiety', '如何应对焦虑情绪', '学习焦虑管理技巧与具体应对步骤。', 'knowledge', 'article', 'healing_contents', '33334444-4444-4444-4444-444444444444', '/healing?tab=knowledge&materialId=10000000-0000-0000-0000-000000000006', 10, 'countdown', JSON_ARRAY('焦虑','科普'), JSON_OBJECT(), TRUE),
  ('10000000-0000-0000-0000-000000000007', 'knowledge-cbt', '认知行为疗法(CBT)介绍', '理解想法、情绪与行为之间的关系。', 'knowledge', 'article', 'healing_contents', '66667777-7777-7777-7777-777777777777', '/healing?tab=knowledge&materialId=10000000-0000-0000-0000-000000000007', 10, 'countdown', JSON_ARRAY('CBT','认知'), JSON_OBJECT(), TRUE),
  ('10000000-0000-0000-0000-000000000008', 'knowledge-sleep-video', '睡眠与心理健康', '通过视频了解睡眠对情绪和冲动控制的影响。', 'knowledge', 'video', 'healing_contents', '55556666-6666-6666-6666-666666666666', '/healing?tab=knowledge&materialId=10000000-0000-0000-0000-000000000008', 10, 'countdown', JSON_ARRAY('睡眠','视频'), JSON_OBJECT(), TRUE),
  ('10000000-0000-0000-0000-000000000009', 'knowledge-exercise-video', '运动与心理健康', '通过视频了解运动对心理健康的积极影响。', 'knowledge', 'video', 'healing_contents', '88889999-9999-9999-9999-999999999999', '/healing?tab=knowledge&materialId=10000000-0000-0000-0000-000000000009', 10, 'countdown', JSON_ARRAY('运动','视频'), JSON_OBJECT(), TRUE),
  ('10000000-0000-0000-0000-000000000010', 'knowledge-family-support', '家人如何支持抑郁症患者', '了解支持性沟通和日常陪伴方式。', 'knowledge', 'article', 'healing_contents', 'aaaabbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '/healing?tab=knowledge&materialId=10000000-0000-0000-0000-000000000010', 10, 'countdown', JSON_ARRAY('家属支持','科普'), JSON_OBJECT(), TRUE),
  ('10000000-0000-0000-0000-000000000011', 'game-temple-run', 'Temple Run 2 跑酷体验', '轻量行为激活任务，进入游戏并完成短时体验。', 'game', 'external', NULL, NULL, '/healing?tab=game', 10, 'countdown', JSON_ARRAY('游戏','行为激活'), JSON_OBJECT('externalUrl','https://poki.com/zh/g/temple-run-2-holi-festival#fullscreen'), TRUE),
  ('10000000-0000-0000-0000-000000000012', 'brain-light', '光调控模拟训练', '脑机干预预留入口，本期用于模拟完成记录。', 'brain_intervention', 'light', NULL, NULL, '/brain-intervention/light', 10, 'countdown', JSON_ARRAY('脑机','光调控'), JSON_OBJECT('mode','light'), TRUE),
  ('10000000-0000-0000-0000-000000000013', 'brain-magnetic', '磁调控模拟训练', '脑机干预预留入口，本期用于模拟完成记录。', 'brain_intervention', 'magnetic', NULL, NULL, '/brain-intervention/magnetic', 10, 'countdown', JSON_ARRAY('脑机','磁调控'), JSON_OBJECT('mode','magnetic'), TRUE),
  ('10000000-0000-0000-0000-000000000014', 'brain-bci', '脑机接口调控模拟训练', '脑机干预预留入口，本期用于模拟完成记录。', 'brain_intervention', 'bci', NULL, NULL, '/brain-intervention/bci', 10, 'countdown', JSON_ARRAY('脑机','接口调控'), JSON_OBJECT('mode','bci'), TRUE)
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  category = VALUES(category),
  subtype = VALUES(subtype),
  target_ref_table = VALUES(target_ref_table),
  target_ref_id = VALUES(target_ref_id),
  route_path = VALUES(route_path),
  duration_sec = VALUES(duration_sec),
  completion_mode = VALUES(completion_mode),
  tags = VALUES(tags),
  config_json = VALUES(config_json),
  is_active = VALUES(is_active);

INSERT INTO intervention_plan_templates (
  id, code, title, risk_level, description, duration_days, daily_required_count, auto_assign_enabled, status
) VALUES
  ('20000000-0000-0000-0000-000000000001', 'default-low-risk', '低风险稳定维护计划', 'low', '维持稳定状态，建立每日情绪记录和轻量放松习惯。', 7, 1, TRUE, 'active'),
  ('20000000-0000-0000-0000-000000000002', 'default-middle-risk', '中风险情绪调节计划', 'middle', '加强情绪识别、冲动控制和压力调节。', 14, 2, TRUE, 'active'),
  ('20000000-0000-0000-0000-000000000003', 'default-high-risk', '高风险强化稳定计划', 'high', '提高随访频率，强化稳定化任务；不能替代专业诊疗。', 14, 3, TRUE, 'active')
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  duration_days = VALUES(duration_days),
  daily_required_count = VALUES(daily_required_count),
  auto_assign_enabled = VALUES(auto_assign_enabled),
  status = VALUES(status);

INSERT INTO intervention_plan_template_items (
  id, template_id, material_id, title, frequency_type, required_count, duration_sec, order_no, required, config_json
) VALUES
  ('21000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '心情日记', 'daily', 1, 0, 1, TRUE, JSON_OBJECT()),
  ('21000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000002', '焦虑缓解呼吸法', 'daily', 1, 10, 2, TRUE, JSON_OBJECT()),
  ('21000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000006', '如何应对焦虑情绪', 'once', 1, 10, 3, FALSE, JSON_OBJECT()),
  ('21000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000009', '运动与心理健康', 'once', 1, 10, 4, FALSE, JSON_OBJECT()),
  ('22000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', '心情日记', 'daily', 1, 0, 1, TRUE, JSON_OBJECT()),
  ('22000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000004', '身体扫描冥想', 'daily', 1, 10, 2, TRUE, JSON_OBJECT()),
  ('22000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000005', '专注力训练', 'weekly', 3, 10, 3, TRUE, JSON_OBJECT()),
  ('22000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000007', '认知行为疗法(CBT)介绍', 'once', 1, 10, 4, FALSE, JSON_OBJECT()),
  ('22000000-0000-0000-0000-000000000005', '20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000008', '睡眠与心理健康', 'once', 1, 10, 5, FALSE, JSON_OBJECT()),
  ('22000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000011', 'Temple Run 2 跑酷体验', 'weekly', 3, 10, 6, FALSE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '心情日记', 'daily', 1, 0, 1, TRUE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', '焦虑缓解呼吸法', 'daily', 1, 10, 2, TRUE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', '睡前放松引导', 'daily', 1, 10, 3, TRUE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000004', '身体扫描冥想', 'weekly', 3, 10, 4, TRUE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000005', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000010', '家人如何支持抑郁症患者', 'once', 1, 10, 5, FALSE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000006', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000008', '睡眠与心理健康', 'once', 1, 10, 6, FALSE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000007', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000012', '光调控模拟训练', 'daily', 1, 10, 7, TRUE, JSON_OBJECT()),
  ('23000000-0000-0000-0000-000000000008', '20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000014', '脑机接口调控模拟训练', 'daily', 1, 10, 8, TRUE, JSON_OBJECT())
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  frequency_type = VALUES(frequency_type),
  required_count = VALUES(required_count),
  duration_sec = VALUES(duration_sec),
  order_no = VALUES(order_no),
  required = VALUES(required),
  config_json = VALUES(config_json);
