-- Legacy Chuxin schema and synthetic test rows. Load into a new, empty MySQL schema.
-- For the current application schema use backend Flyway migrations instead.
SET @fixture_old_foreign_key_checks = @@SESSION.FOREIGN_KEY_CHECKS;
SET SESSION FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `assessments` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `assessment_type` varchar(255) NOT NULL DEFAULT 'multimodal',
  `conversation_history` json NOT NULL DEFAULT (json_array()),
  `text_input` text,
  `voice_input_url` text,
  `image_input_url` text,
  `video_input_url` text,
  `ai_analysis` json DEFAULT NULL,
  `risk_level` int DEFAULT '0',
  `score` int DEFAULT NULL,
  `report` json DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_assessments_user_created` (`user_id`,`created_at` DESC),
  CONSTRAINT `fk_assessments_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `auth_users` (
  `id` varchar(36) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `password_hash` varchar(100) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `username` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_auth_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `community_comments` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `post_id` char(36) NOT NULL,
  `user_id` char(36) NOT NULL,
  `anonymous_name` varchar(255) NOT NULL,
  `content` text NOT NULL,
  `like_count` int NOT NULL DEFAULT '0',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_community_comments_post` (`post_id`,`created_at` DESC),
  KEY `idx_community_comments_user` (`user_id`),
  CONSTRAINT `fk_community_comments_post` FOREIGN KEY (`post_id`) REFERENCES `community_posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_community_comments_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `community_posts` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `anonymous_name` varchar(255) NOT NULL,
  `title` text NOT NULL,
  `content` text NOT NULL,
  `tags` json DEFAULT NULL,
  `like_count` int NOT NULL DEFAULT '0',
  `comment_count` int NOT NULL DEFAULT '0',
  `is_pinned` tinyint(1) NOT NULL DEFAULT '0',
  `is_hidden` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `category_id` char(36) DEFAULT NULL,
  `is_recovery_story` tinyint(1) DEFAULT '0',
  `is_featured` tinyint(1) DEFAULT '0',
  `anonymous_nickname` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_community_posts_created` (`created_at` DESC),
  KEY `idx_community_posts_category_id` (`category_id`),
  KEY `idx_community_posts_is_recovery_story` (`is_recovery_story`),
  KEY `idx_community_posts_user` (`user_id`),
  CONSTRAINT `fk_community_posts_category` FOREIGN KEY (`category_id`) REFERENCES `post_categories` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_community_posts_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `doctor_patients` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `doctor_id` char(36) NOT NULL,
  `patient_id` char(36) NOT NULL,
  `status` varchar(64) NOT NULL DEFAULT 'active',
  `notes` text,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_doctor_patients_doctor_patient` (`doctor_id`,`patient_id`),
  KEY `idx_doctor_patients_doctor` (`doctor_id`,`status`),
  KEY `idx_doctor_patients_patient` (`patient_id`),
  CONSTRAINT `fk_doctor_patients_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_doctor_patients_patient` FOREIGN KEY (`patient_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `doctor_verification_codes` (
  `id` varchar(36) NOT NULL,
  `code` varchar(255) NOT NULL,
  `is_permanent` tinyint(1) NOT NULL DEFAULT '0',
  `is_used` tinyint(1) NOT NULL DEFAULT '0',
  `used_by` char(36) DEFAULT NULL,
  `used_at` timestamp(6) NULL DEFAULT NULL,
  `created_by` char(36) DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `notes` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_doctor_verification_codes_code` (`code`),
  KEY `idx_verification_codes_code` (`code`),
  KEY `idx_verification_codes_is_used` (`is_used`),
  KEY `idx_verification_codes_created_by` (`created_by`),
  KEY `idx_verification_codes_used_by` (`used_by`),
  CONSTRAINT `fk_verification_codes_created_by` FOREIGN KEY (`created_by`) REFERENCES `profiles` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_verification_codes_used_by` FOREIGN KEY (`used_by`) REFERENCES `profiles` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Supabase auth.users(id) used_by is represented by profiles.id.';

CREATE TABLE `emotion_diaries` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `diary_date` date NOT NULL DEFAULT (curdate()),
  `emotion_level` enum('very_bad','bad','neutral','good','very_good') NOT NULL,
  `title` text,
  `content` text,
  `tags` json DEFAULT NULL,
  `ai_analysis` json DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `image_urls` json DEFAULT NULL,
  `voice_url` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_emotion_diaries_user_date` (`user_id`,`diary_date`),
  KEY `idx_emotion_diaries_user_date` (`user_id`,`diary_date` DESC),
  CONSTRAINT `fk_emotion_diaries_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `healing_contents` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `title` text NOT NULL,
  `description` text,
  `category` varchar(255) NOT NULL,
  `content_type` varchar(128) NOT NULL,
  `content_url` text,
  `duration` int DEFAULT NULL,
  `thumbnail_url` text,
  `tags` json DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `view_count` int NOT NULL DEFAULT '0',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `author` varchar(255) DEFAULT NULL,
  `like_count` int DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_healing_contents_category` (`category`,`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `knowledge_base` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `title` text NOT NULL,
  `content` text NOT NULL,
  `category` varchar(255) NOT NULL,
  `tags` json DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_by` char(36) DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `content_type` varchar(128) DEFAULT 'text',
  `file_url` text,
  `file_name` varchar(255) DEFAULT NULL,
  `file_size` int DEFAULT NULL,
  `file_mime_type` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_knowledge_base_category` (`category`,`is_active`),
  KEY `idx_knowledge_base_content_type` (`content_type`),
  KEY `idx_knowledge_base_created_by` (`created_by`),
  KEY `idx_knowledge_base_file_url` ((cast(`file_url` as char(255) charset utf8mb4))),
  CONSTRAINT `fk_knowledge_base_created_by` FOREIGN KEY (`created_by`) REFERENCES `profiles` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `meditation_sessions` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `content_id` char(36) NOT NULL,
  `duration` int NOT NULL,
  `completed` tinyint(1) DEFAULT '0',
  `mood_before` varchar(255) DEFAULT NULL,
  `mood_after` varchar(255) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_meditation_sessions_user_id` (`user_id`),
  KEY `idx_meditation_sessions_created_at` (`created_at` DESC),
  KEY `idx_meditation_sessions_content` (`content_id`),
  CONSTRAINT `fk_meditation_sessions_content` FOREIGN KEY (`content_id`) REFERENCES `healing_contents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_meditation_sessions_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Supabase auth.users(id) user_id is represented by profiles.id.';

CREATE TABLE `post_categories` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `name` varchar(255) NOT NULL,
  `description` text,
  `icon` varchar(255) DEFAULT NULL,
  `color` varchar(64) DEFAULT NULL,
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `post_likes` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `post_id` char(36) NOT NULL,
  `user_id` char(36) NOT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_likes_post_user` (`post_id`,`user_id`),
  KEY `idx_post_likes_user` (`user_id`),
  CONSTRAINT `fk_post_likes_post` FOREIGN KEY (`post_id`) REFERENCES `community_posts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_post_likes_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `profile_emotion_record_triggers` (
  `record_id` bigint NOT NULL,
  `trigger_text` varchar(64) NOT NULL,
  KEY `FKjse3whetbh305062radn2uhij` (`record_id`),
  CONSTRAINT `FKjse3whetbh305062radn2uhij` FOREIGN KEY (`record_id`) REFERENCES `profile_emotion_records` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `profile_emotion_records` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` varchar(2000) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `record_date` date NOT NULL,
  `mood` varchar(32) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `profile_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `FKslhy34d20jfdaipv5tnk1v2qb` (`profile_id`),
  CONSTRAINT `FKslhy34d20jfdaipv5tnk1v2qb` FOREIGN KEY (`profile_id`) REFERENCES `profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `profiles` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `username` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(64) DEFAULT NULL,
  `role` varchar(16) NOT NULL,
  `avatar_url` varchar(255) DEFAULT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `gender` varchar(64) DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `wechat` varchar(255) DEFAULT NULL,
  `bio` text,
  `background_url` text,
  `selected_background` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_profiles_username` (`username`),
  KEY `idx_profiles_username` (`username`),
  KEY `idx_profiles_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='User profiles. Supabase auth.users(id) is represented by profiles.id.';

CREATE TABLE `risk_alerts` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `patient_id` char(36) NOT NULL,
  `alert_type` varchar(255) NOT NULL,
  `risk_level` int NOT NULL,
  `description` text NOT NULL,
  `data_source` varchar(255) DEFAULT NULL,
  `source_id` char(36) DEFAULT NULL,
  `is_handled` tinyint(1) NOT NULL DEFAULT '0',
  `handled_by` char(36) DEFAULT NULL,
  `handled_at` timestamp(6) NULL DEFAULT NULL,
  `notes` text,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_risk_alerts_patient` (`patient_id`,`created_at` DESC),
  KEY `idx_risk_alerts_handled` (`is_handled`,`created_at` DESC),
  KEY `idx_risk_alerts_handled_by` (`handled_by`),
  CONSTRAINT `fk_risk_alerts_handled_by` FOREIGN KEY (`handled_by`) REFERENCES `profiles` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_risk_alerts_patient` FOREIGN KEY (`patient_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_favorites` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `content_id` char(36) NOT NULL,
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_favorites_user_content` (`user_id`,`content_id`),
  KEY `idx_user_favorites_user_id` (`user_id`),
  KEY `idx_user_favorites_content` (`content_id`),
  CONSTRAINT `fk_user_favorites_content` FOREIGN KEY (`content_id`) REFERENCES `healing_contents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_favorites_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Supabase auth.users(id) user_id is represented by profiles.id.';

CREATE TABLE `user_healing_records` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `healing_content_id` char(36) NOT NULL,
  `duration_seconds` int DEFAULT NULL,
  `completed` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `idx_user_healing_records_user` (`user_id`,`created_at` DESC),
  KEY `idx_user_healing_records_content` (`healing_content_id`),
  CONSTRAINT `fk_user_healing_records_content` FOREIGN KEY (`healing_content_id`) REFERENCES `healing_contents` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_healing_records_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `wearable_data` (
  `id` char(36) NOT NULL DEFAULT (uuid()),
  `user_id` char(36) NOT NULL,
  `record_date` date NOT NULL DEFAULT (curdate()),
  `heart_rate` int DEFAULT NULL,
  `sleep_hours` decimal(4,2) DEFAULT NULL,
  `sleep_quality` int DEFAULT NULL,
  `steps` int DEFAULT NULL,
  `calories` int DEFAULT NULL,
  `stress_level` int DEFAULT NULL,
  `data_json` json DEFAULT NULL,
  `created_at` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `blood_oxygen` int DEFAULT NULL,
  `temperature` decimal(4,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_wearable_data_user_date` (`user_id`,`record_date`),
  KEY `idx_wearable_data_user_date` (`user_id`,`record_date` DESC),
  KEY `idx_wearable_data_blood_oxygen` (`blood_oxygen`),
  KEY `idx_wearable_data_temperature` (`temperature`),
  CONSTRAINT `fk_wearable_data_user` FOREIGN KEY (`user_id`) REFERENCES `profiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET SESSION FOREIGN_KEY_CHECKS = @fixture_old_foreign_key_checks;

CREATE SQL SECURITY INVOKER VIEW `public_profiles` AS
SELECT `id`, `username`, `avatar_url`, `full_name`, `role` FROM `profiles`;

-- Preserve the legacy role mix and profile links without usable credentials.
START TRANSACTION;
INSERT INTO `auth_users` (`id`, `created_at`, `password_hash`, `updated_at`, `username`) VALUES
  ('10000000-0000-4000-8000-000000000001', '2026-01-01 00:00:00', 'FIXTURE_LOGIN_DISABLED', '2026-01-01 00:00:00', 'fixture_user_1'),
  ('10000000-0000-4000-8000-000000000002', '2026-01-01 00:00:00', 'FIXTURE_LOGIN_DISABLED', '2026-01-01 00:00:00', 'fixture_admin'),
  ('10000000-0000-4000-8000-000000000003', '2026-01-01 00:00:00', 'FIXTURE_LOGIN_DISABLED', '2026-01-01 00:00:00', 'fixture_user_2'),
  ('10000000-0000-4000-8000-000000000004', '2026-01-01 00:00:00', 'FIXTURE_LOGIN_DISABLED', '2026-01-01 00:00:00', 'fixture_doctor');

INSERT INTO `profiles` (`id`, `username`, `email`, `role`) VALUES
  ('10000000-0000-4000-8000-000000000001', 'fixture_user_1', 'user1@example.invalid', 'user'),
  ('10000000-0000-4000-8000-000000000002', 'fixture_admin', 'admin@example.invalid', 'admin'),
  ('10000000-0000-4000-8000-000000000003', 'fixture_user_2', 'user2@example.invalid', 'user'),
  ('10000000-0000-4000-8000-000000000004', 'fixture_doctor', 'doctor@example.invalid', 'doctor');

INSERT INTO `doctor_verification_codes` (`id`, `code`, `is_permanent`, `is_used`, `used_by`, `used_at`, `created_by`, `notes`) VALUES
  ('10000000-0000-4000-8000-000000000005', 'FIXTURE_CODE_DISABLED', 0, 1,
   '10000000-0000-4000-8000-000000000004', '2026-01-01 00:00:00',
   '10000000-0000-4000-8000-000000000002', 'Synthetic, already used');
COMMIT;
