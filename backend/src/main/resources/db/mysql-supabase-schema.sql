-- MySQL 8.0 compatible schema converted from C:\Users\Dell\Desktop\docs Supabase backup.
-- Keeps the original business table and column names for API migration compatibility.

CREATE DATABASE IF NOT EXISTS chuxin
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE chuxin;

CREATE TABLE IF NOT EXISTS profiles (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NULL,
  phone VARCHAR(64) NULL,
  role ENUM('user', 'doctor', 'admin') NOT NULL DEFAULT 'user',
  avatar_url TEXT NULL,
  full_name VARCHAR(255) NULL,
  gender VARCHAR(64) NULL,
  birth_date DATE NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  wechat VARCHAR(255) NULL,
  bio TEXT NULL,
  background_url TEXT NULL,
  selected_background TEXT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_profiles_username (username),
  KEY idx_profiles_username (username),
  KEY idx_profiles_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='User profiles. Supabase auth.users(id) is represented by profiles.id.';

CREATE TABLE IF NOT EXISTS auth_users (
  id CHAR(36) NOT NULL,
  username VARCHAR(255) NOT NULL,
  password_hash VARCHAR(100) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_auth_users_username (username),
  CONSTRAINT fk_auth_users_profile FOREIGN KEY (id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Local replacement for Supabase auth.users credentials. id matches profiles.id.';

CREATE TABLE IF NOT EXISTS healing_contents (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  title TEXT NOT NULL,
  description TEXT NULL,
  category VARCHAR(255) NOT NULL,
  content_type VARCHAR(128) NOT NULL,
  content_url TEXT NULL,
  duration INT NULL,
  thumbnail_url TEXT NULL,
  tags JSON NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  view_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  author VARCHAR(255) NULL,
  like_count INT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_healing_contents_category (category, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS post_categories (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  name VARCHAR(255) NOT NULL,
  description TEXT NULL,
  icon VARCHAR(255) NULL,
  color VARCHAR(64) NULL,
  created_at TIMESTAMP(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_post_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS emotion_diaries (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  diary_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  emotion_level ENUM('very_bad', 'bad', 'neutral', 'good', 'very_good') NOT NULL,
  title TEXT NULL,
  content TEXT NULL,
  tags JSON NULL,
  ai_analysis JSON NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  image_urls JSON NULL,
  voice_url TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_emotion_diaries_user_date (user_id, diary_date DESC),
  CONSTRAINT fk_emotion_diaries_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS profile_emotion_records (
  id BIGINT NOT NULL AUTO_INCREMENT,
  profile_id CHAR(36) NOT NULL,
  record_date DATE NOT NULL,
  mood VARCHAR(32) NOT NULL,
  content VARCHAR(2000) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_profile_emotion_records_profile_created (profile_id, created_at DESC, id DESC),
  CONSTRAINT fk_profile_emotion_records_profile FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Vue/Spring emotion record API storage; multiple records per profile per day are allowed.';

CREATE TABLE IF NOT EXISTS profile_emotion_record_triggers (
  record_id BIGINT NOT NULL,
  trigger_text VARCHAR(64) NOT NULL,
  KEY idx_profile_emotion_record_triggers_record (record_id),
  CONSTRAINT fk_profile_emotion_record_triggers_record FOREIGN KEY (record_id) REFERENCES profile_emotion_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS assessments (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  assessment_type VARCHAR(255) NOT NULL DEFAULT 'multimodal',
  conversation_history JSON NOT NULL DEFAULT (JSON_ARRAY()),
  text_input TEXT NULL,
  voice_input_url TEXT NULL,
  image_input_url TEXT NULL,
  video_input_url TEXT NULL,
  ai_analysis JSON NULL,
  risk_level INT NULL DEFAULT 0,
  score INT NULL,
  report JSON NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_assessments_user_created (user_id, created_at DESC),
  CONSTRAINT fk_assessments_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS wearable_data (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  record_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  heart_rate INT NULL,
  sleep_hours DECIMAL(4,2) NULL,
  sleep_quality INT NULL,
  steps INT NULL,
  calories INT NULL,
  stress_level INT NULL,
  data_json JSON NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  blood_oxygen INT NULL,
  temperature DECIMAL(4,2) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_wearable_data_user_date (user_id, record_date),
  KEY idx_wearable_data_user_date (user_id, record_date DESC),
  KEY idx_wearable_data_blood_oxygen (blood_oxygen),
  KEY idx_wearable_data_temperature (temperature),
  CONSTRAINT fk_wearable_data_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS user_healing_records (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  healing_content_id CHAR(36) NOT NULL,
  duration_seconds INT NULL,
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_user_healing_records_user (user_id, created_at DESC),
  KEY idx_user_healing_records_content (healing_content_id),
  CONSTRAINT fk_user_healing_records_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_healing_records_content FOREIGN KEY (healing_content_id) REFERENCES healing_contents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS community_posts (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  anonymous_name VARCHAR(255) NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  tags JSON NULL,
  like_count INT NOT NULL DEFAULT 0,
  comment_count INT NOT NULL DEFAULT 0,
  is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
  is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  category_id CHAR(36) NULL,
  is_recovery_story BOOLEAN NULL DEFAULT FALSE,
  is_featured BOOLEAN NULL DEFAULT FALSE,
  anonymous_nickname VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_community_posts_created (created_at DESC),
  KEY idx_community_posts_category_id (category_id),
  KEY idx_community_posts_is_recovery_story (is_recovery_story),
  KEY idx_community_posts_user (user_id),
  CONSTRAINT fk_community_posts_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE,
  CONSTRAINT fk_community_posts_category FOREIGN KEY (category_id) REFERENCES post_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS community_comments (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  post_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  anonymous_name VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  like_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_community_comments_post (post_id, created_at DESC),
  KEY idx_community_comments_user (user_id),
  CONSTRAINT fk_community_comments_post FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_community_comments_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS post_likes (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  post_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_post_likes_post_user (post_id, user_id),
  KEY idx_post_likes_user (user_id),
  CONSTRAINT fk_post_likes_post FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_post_likes_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS doctor_patients (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  doctor_id CHAR(36) NOT NULL,
  patient_id CHAR(36) NOT NULL,
  status VARCHAR(64) NOT NULL DEFAULT 'active',
  notes TEXT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_doctor_patients_doctor_patient (doctor_id, patient_id),
  KEY idx_doctor_patients_doctor (doctor_id, status),
  KEY idx_doctor_patients_patient (patient_id),
  CONSTRAINT fk_doctor_patients_doctor FOREIGN KEY (doctor_id) REFERENCES profiles(id) ON DELETE CASCADE,
  CONSTRAINT fk_doctor_patients_patient FOREIGN KEY (patient_id) REFERENCES profiles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS risk_alerts (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  patient_id CHAR(36) NOT NULL,
  alert_type VARCHAR(255) NOT NULL,
  risk_level INT NOT NULL,
  description TEXT NOT NULL,
  data_source VARCHAR(255) NULL,
  source_id CHAR(36) NULL,
  is_handled BOOLEAN NOT NULL DEFAULT FALSE,
  handled_by CHAR(36) NULL,
  handled_at TIMESTAMP(6) NULL,
  notes TEXT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_risk_alerts_patient (patient_id, created_at DESC),
  KEY idx_risk_alerts_handled (is_handled, created_at DESC),
  KEY idx_risk_alerts_handled_by (handled_by),
  CONSTRAINT fk_risk_alerts_patient FOREIGN KEY (patient_id) REFERENCES profiles(id) ON DELETE CASCADE,
  CONSTRAINT fk_risk_alerts_handled_by FOREIGN KEY (handled_by) REFERENCES profiles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS knowledge_base (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  category VARCHAR(255) NOT NULL,
  tags JSON NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_by CHAR(36) NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  content_type VARCHAR(128) NULL DEFAULT 'text',
  file_url TEXT NULL,
  file_name VARCHAR(255) NULL,
  file_size INT NULL,
  file_mime_type VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_knowledge_base_category (category, is_active),
  KEY idx_knowledge_base_content_type (content_type),
  KEY idx_knowledge_base_file_url ((CAST(file_url AS CHAR(255)))),
  KEY idx_knowledge_base_created_by (created_by),
  CONSTRAINT fk_knowledge_base_created_by FOREIGN KEY (created_by) REFERENCES profiles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS meditation_sessions (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  content_id CHAR(36) NOT NULL,
  duration INT NOT NULL,
  completed BOOLEAN NULL DEFAULT FALSE,
  mood_before VARCHAR(255) NULL,
  mood_after VARCHAR(255) NULL,
  notes TEXT NULL,
  created_at TIMESTAMP(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_meditation_sessions_user_id (user_id),
  KEY idx_meditation_sessions_created_at (created_at DESC),
  KEY idx_meditation_sessions_content (content_id),
  CONSTRAINT fk_meditation_sessions_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE,
  CONSTRAINT fk_meditation_sessions_content FOREIGN KEY (content_id) REFERENCES healing_contents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Supabase auth.users(id) user_id is represented by profiles.id.';

CREATE TABLE IF NOT EXISTS user_favorites (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  content_id CHAR(36) NOT NULL,
  created_at TIMESTAMP(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_favorites_user_content (user_id, content_id),
  KEY idx_user_favorites_user_id (user_id),
  KEY idx_user_favorites_content (content_id),
  CONSTRAINT fk_user_favorites_user FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_favorites_content FOREIGN KEY (content_id) REFERENCES healing_contents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Supabase auth.users(id) user_id is represented by profiles.id.';

CREATE TABLE IF NOT EXISTS doctor_verification_codes (
  id CHAR(36) NOT NULL DEFAULT (UUID()),
  code VARCHAR(255) NOT NULL,
  is_permanent BOOLEAN NOT NULL DEFAULT FALSE,
  is_used BOOLEAN NOT NULL DEFAULT FALSE,
  used_by CHAR(36) NULL,
  used_at TIMESTAMP(6) NULL,
  created_by CHAR(36) NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  notes TEXT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_doctor_verification_codes_code (code),
  KEY idx_verification_codes_code (code),
  KEY idx_verification_codes_is_used (is_used),
  KEY idx_verification_codes_created_by (created_by),
  KEY idx_verification_codes_used_by (used_by),
  CONSTRAINT fk_verification_codes_created_by FOREIGN KEY (created_by) REFERENCES profiles(id) ON DELETE SET NULL,
  CONSTRAINT fk_verification_codes_used_by FOREIGN KEY (used_by) REFERENCES profiles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Supabase auth.users(id) used_by is represented by profiles.id.';

CREATE OR REPLACE VIEW public_profiles AS
SELECT id, username, avatar_url, full_name, role
FROM profiles;

INSERT INTO doctor_verification_codes (id, code, is_permanent, is_used, notes)
VALUES (UUID(), '2026', TRUE, FALSE, '默认永久有效验证码')
ON DUPLICATE KEY UPDATE is_permanent = TRUE, notes = '默认永久有效验证码';
