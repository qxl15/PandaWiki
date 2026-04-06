"""服务端核心数据模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ClientUser(Base):
    __tablename__ = "client_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="admin")
    device_fingerprint: Mapped[str] = mapped_column(String(128), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oa_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str] = mapped_column(String(128), default="")
    title: Mapped[str] = mapped_column(String(128), default="")
    group_id: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    contact_encrypted: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AttendanceGroup(Base):
    __tablename__ = "attendance_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    group_name: Mapped[str] = mapped_column(String(128))
    on_duty_time: Mapped[str] = mapped_column(String(8), default="09:00")
    off_duty_time: Mapped[str] = mapped_column(String(8), default="18:00")
    late_threshold_min: Mapped[int] = mapped_column(Integer, default=30)
    early_threshold_min: Mapped[int] = mapped_column(Integer, default=30)
    missing_card_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oa_record_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    oa_user_id: Mapped[str] = mapped_column(String(64), index=True)
    punch_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    punch_type: Mapped[str] = mapped_column(String(32), default="on_duty")
    status: Mapped[str] = mapped_column(String(32), default="normal")
    group_id: Mapped[str] = mapped_column(String(64), default="")


class AbnormalEvent(Base):
    __tablename__ = "abnormal_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oa_user_id: Mapped[str] = mapped_column(String(64), index=True)
    event_date: Mapped[str] = mapped_column(String(10), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default="")
    handled: Mapped[bool] = mapped_column(Boolean, default=False)
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("idx_record_user_time", AttendanceRecord.oa_user_id, AttendanceRecord.punch_time)
Index("idx_abnormal_user_date", AbnormalEvent.oa_user_id, AbnormalEvent.event_date)
