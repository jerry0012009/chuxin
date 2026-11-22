CREATE TABLE IF NOT EXISTS departments (
  id CHAR(36) PRIMARY KEY,
  name VARCHAR(128) NOT NULL UNIQUE,
  description TEXT NULL,
  status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO departments (id, name, description, status, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  '默认部门',
  '系统默认部门',
  'active',
  CURRENT_TIMESTAMP(3),
  CURRENT_TIMESTAMP(3)
)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  status = VALUES(status),
  updated_at = CURRENT_TIMESTAMP(3);

ALTER TABLE users MODIFY role ENUM('user', 'doctor', 'admin', 'super_admin') NOT NULL DEFAULT 'user';
ALTER TABLE profiles MODIFY role ENUM('user', 'doctor', 'admin', 'super_admin') NOT NULL DEFAULT 'user';

ALTER TABLE users
  ADD COLUMN super_admin_unique TINYINT
    GENERATED ALWAYS AS (CASE WHEN role = 'super_admin' THEN 1 ELSE NULL END) STORED,
  ADD UNIQUE KEY uk_users_single_super_admin (super_admin_unique);

ALTER TABLE profiles
  ADD COLUMN department_id CHAR(36) NULL AFTER role;

UPDATE profiles
SET department_id = '00000000-0000-0000-0000-000000000001'
WHERE role = 'user' AND department_id IS NULL;

ALTER TABLE profiles
  ADD CONSTRAINT fk_profiles_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL;

SET @super_admin_id = (SELECT id FROM users WHERE username = 'admin' LIMIT 1);
SET @super_admin_id = COALESCE(@super_admin_id, UUID());

INSERT INTO users (
  id, username, email, password_hash, role, status, metadata, created_at, updated_at
)
SELECT
  @super_admin_id,
  'admin',
  'admin@chuxin.local',
  '$2b$10$zKLLEg4sxI0nz8mPMW5d4OtPUnsyQLYypH4BXwqHHhriUklnfaf7C',
  'super_admin',
  'active',
  JSON_OBJECT('username', 'admin', 'role', 'super_admin'),
  CURRENT_TIMESTAMP(3),
  CURRENT_TIMESTAMP(3)
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

UPDATE users
SET
  username = 'admin',
  password_hash = '$2b$10$zKLLEg4sxI0nz8mPMW5d4OtPUnsyQLYypH4BXwqHHhriUklnfaf7C',
  role = 'super_admin',
  status = 'active',
  metadata = JSON_OBJECT('username', 'admin', 'role', 'super_admin'),
  updated_at = CURRENT_TIMESTAMP(3)
WHERE id = @super_admin_id;

INSERT INTO profiles (
  id, username, email, role, department_id, phone, wechat, avatar_url, full_name, gender, birth_date, bio,
  background_url, selected_background, created_at, updated_at
)
VALUES (
  @super_admin_id,
  'admin',
  'admin@chuxin.local',
  'super_admin',
  NULL,
  NULL,
  NULL,
  NULL,
  '超级管理员',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  CURRENT_TIMESTAMP(3),
  CURRENT_TIMESTAMP(3)
)
ON DUPLICATE KEY UPDATE
  username = 'admin',
  role = 'super_admin',
  full_name = COALESCE(full_name, VALUES(full_name)),
  updated_at = CURRENT_TIMESTAMP(3);
