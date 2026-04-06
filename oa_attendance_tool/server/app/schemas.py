"""接口入参与出参定义。"""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    device_fingerprint: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SyncRequest(BaseModel):
    full_sync: bool = True


class QueryRequest(BaseModel):
    group_id: str
    start_date: str
    end_date: str


class RuleUpdateRequest(BaseModel):
    group_id: str
    late_threshold_min: int = Field(ge=0, le=240)
    early_threshold_min: int = Field(ge=0, le=240)
    remind_channel: str = "desktop"
    remind_frequency: str = "realtime"


class EventHandleRequest(BaseModel):
    event_id: int
    remark: str = ""


class AttendanceRow(BaseModel):
    oa_user_id: str
    name: str
    punch_time: datetime
    punch_type: str
    status: str


class HealthResponse(BaseModel):
    status: str
    server_time: datetime
