-- 通达OA考勤工具服务端数据库脚本（SQLite/MySQL兼容风格，部分语法按实际数据库微调）

CREATE TABLE IF NOT EXISTS client_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'admin',
    device_fingerprint VARCHAR(128) NOT NULL DEFAULT '',
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oa_user_id VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(64) NOT NULL,
    department VARCHAR(128) NOT NULL DEFAULT '',
    title VARCHAR(128) NOT NULL DEFAULT '',
    group_id VARCHAR(64) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    contact_encrypted TEXT NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id VARCHAR(64) NOT NULL UNIQUE,
    group_name VARCHAR(128) NOT NULL,
    on_duty_time VARCHAR(8) NOT NULL,
    off_duty_time VARCHAR(8) NOT NULL,
    late_threshold_min INTEGER NOT NULL DEFAULT 30,
    early_threshold_min INTEGER NOT NULL DEFAULT 30,
    missing_card_enabled BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oa_record_id VARCHAR(64) NOT NULL UNIQUE,
    oa_user_id VARCHAR(64) NOT NULL,
    punch_time DATETIME NOT NULL,
    punch_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    group_id VARCHAR(64) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS abnormal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oa_user_id VARCHAR(64) NOT NULL,
    event_date VARCHAR(10) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    duration_min INTEGER NOT NULL DEFAULT 0,
    detail TEXT NOT NULL,
    handled BOOLEAN NOT NULL DEFAULT 0,
    remark TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(16) NOT NULL,
    action VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_record_user_time ON attendance_records (oa_user_id, punch_time);
CREATE INDEX IF NOT EXISTS idx_abnormal_user_date ON abnormal_events (oa_user_id, event_date);
CREATE INDEX IF NOT EXISTS idx_audit_action_time ON audit_logs (action, created_at);
