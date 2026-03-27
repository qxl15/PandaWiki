-- Professional feature foundation schema

-- 1) Node query performance for large knowledge bases (10k docs per KB)
CREATE INDEX IF NOT EXISTS idx_nodes_kb_id_parent_id_position ON public.nodes (kb_id, parent_id, position);
CREATE INDEX IF NOT EXISTS idx_nodes_kb_id_status_updated_at ON public.nodes (kb_id, status, updated_at DESC);

-- 2) Admin RBAC
CREATE TABLE IF NOT EXISTS admin_roles (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  remark TEXT NOT NULL DEFAULT '',
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
  created_by VARCHAR(255) NOT NULL DEFAULT '',
  updated_by VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_roles_name ON admin_roles (name);

CREATE TABLE IF NOT EXISTS admin_role_permissions (
  id BIGSERIAL PRIMARY KEY,
  role_id BIGINT NOT NULL REFERENCES admin_roles(id) ON DELETE CASCADE,
  permission_key VARCHAR(128) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_role_permissions_unique ON admin_role_permissions (role_id, permission_key);

CREATE TABLE IF NOT EXISTS admin_user_roles (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  role_id BIGINT NOT NULL REFERENCES admin_roles(id) ON DELETE CASCADE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_user_roles_unique ON admin_user_roles (user_id, role_id);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  account VARCHAR(255) NOT NULL,
  action VARCHAR(128) NOT NULL,
  target_type VARCHAR(64) NOT NULL,
  target_id VARCHAR(255) NOT NULL DEFAULT '',
  detail JSONB NOT NULL DEFAULT '{}'::jsonb,
  client_ip VARCHAR(64) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_user_id ON admin_audit_logs (user_id, created_at DESC);

-- built-in super admin role (immutable in service layer)
INSERT INTO admin_roles (name, remark, enabled, is_builtin, created_by, updated_by)
SELECT '超级管理员', '系统内置角色，拥有全部后台权限', TRUE, TRUE, 'system', 'system'
WHERE NOT EXISTS (SELECT 1 FROM admin_roles WHERE name = '超级管理员');

-- 3) Copyright settings (global + i18n ready)
CREATE TABLE IF NOT EXISTS site_copyright_settings (
  id BIGSERIAL PRIMARY KEY,
  locale VARCHAR(32) NOT NULL DEFAULT 'zh-CN',
  owner_name VARCHAR(255) NOT NULL DEFAULT '',
  copyright_year VARCHAR(32) NOT NULL DEFAULT '',
  icp_no VARCHAR(128) NOT NULL DEFAULT '',
  statement TEXT NOT NULL DEFAULT '',
  link VARCHAR(500) NOT NULL DEFAULT '',
  show_in_footer BOOLEAN NOT NULL DEFAULT TRUE,
  show_in_doc_detail_footer BOOLEAN NOT NULL DEFAULT TRUE,
  updated_by VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_site_copyright_settings_locale ON site_copyright_settings(locale);

-- 4) AI Prompt templates + versioning
CREATE TABLE IF NOT EXISTS ai_prompt_templates (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  scope VARCHAR(32) NOT NULL DEFAULT 'global', -- global|document|directory
  prompt_content TEXT NOT NULL,
  is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
  created_by VARCHAR(255) NOT NULL DEFAULT '',
  updated_by VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_prompt_templates_name_scope ON ai_prompt_templates(name, scope);

CREATE TABLE IF NOT EXISTS ai_prompt_bindings (
  id BIGSERIAL PRIMARY KEY,
  kb_id VARCHAR(255) NOT NULL,
  scope VARCHAR(32) NOT NULL, -- global|document|directory
  ref_id VARCHAR(255) NOT NULL DEFAULT '', -- doc id / directory id / empty for global
  prompt_content TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_by VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_prompt_bindings_lookup ON ai_prompt_bindings(kb_id, scope, ref_id, is_active);

CREATE TABLE IF NOT EXISTS ai_prompt_binding_histories (
  id BIGSERIAL PRIMARY KEY,
  binding_id BIGINT NOT NULL REFERENCES ai_prompt_bindings(id) ON DELETE CASCADE,
  kb_id VARCHAR(255) NOT NULL,
  scope VARCHAR(32) NOT NULL,
  ref_id VARCHAR(255) NOT NULL DEFAULT '',
  prompt_content TEXT NOT NULL,
  version INT NOT NULL,
  created_by VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_prompt_binding_histories_binding_id ON ai_prompt_binding_histories(binding_id, version DESC);
