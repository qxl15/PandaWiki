"""通达OA考勤安全服务端入口。"""

from __future__ import annotations

from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import (
    AbnormalEvent,
    AttendanceGroup,
    AttendanceRecord,
    AuditLog,
    ClientUser,
    Employee,
)
from .oa_client import TongdaOAClient, to_iso
from .rule_engine import build_abnormal_events
from .schemas import (
    EventHandleRequest,
    HealthResponse,
    LoginRequest,
    QueryRequest,
    RuleUpdateRequest,
    SyncRequest,
    TokenResponse,
)
from .security import calc_device_fingerprint, create_access_token, encrypt_text, hash_password, verify_password

app = FastAPI(title=settings.app_name)
security = HTTPBearer()
oa_client = TongdaOAClient()
scheduler = BackgroundScheduler()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(sync_job, "interval", minutes=30, id="sync_job", replace_existing=True)
    scheduler.start()
    with Session(engine) as db:
        seed_admin_if_needed(db)


@app.on_event("shutdown")
def shutdown() -> None:
    scheduler.shutdown(wait=False)


def seed_admin_if_needed(db: Session) -> None:
    admin = db.scalar(select(ClientUser).where(ClientUser.username == "admin"))
    if admin:
        return
    # 注意：首次部署后请立即登录并修改默认密码。
    db.add(ClientUser(username="admin", password_hash=hash_password("ChangeMe123!"), role="admin"))
    db.commit()


def write_log(db: Session, level: str, action: str, message: str) -> None:
    db.add(AuditLog(level=level, action=action, message=message))
    db.commit()


def verify_client_ip(request: Request) -> None:
    allowed = {ip.strip() for ip in settings.allowed_client_ips.split(",") if ip.strip()}
    client_ip = request.client.host if request.client else ""
    if allowed and client_ip not in allowed:
        raise HTTPException(status_code=403, detail="客户端IP不在白名单")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> ClientUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub", "")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token 无效") from exc

    user = db.scalar(select(ClientUser).where(ClientUser.username == username, ClientUser.enabled.is_(True)))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", server_time=datetime.utcnow())


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    verify_client_ip(request)
    user = db.scalar(select(ClientUser).where(ClientUser.username == payload.username, ClientUser.enabled.is_(True)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    fp = calc_device_fingerprint(payload.device_fingerprint)
    if user.device_fingerprint and user.device_fingerprint != fp:
        raise HTTPException(status_code=403, detail="设备未授权")
    if not user.device_fingerprint:
        user.device_fingerprint = fp
        db.commit()

    token = create_access_token(user.username)
    write_log(db, "INFO", "login", f"用户 {user.username} 登录成功")
    return TokenResponse(access_token=token)


@app.post("/api/sync")
async def manual_sync(
    payload: SyncRequest,
    _: ClientUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    del payload
    await do_sync(db)
    return {"message": "同步完成"}


@app.post("/api/rules")
def update_rule(
    payload: RuleUpdateRequest,
    _: ClientUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    group = db.scalar(select(AttendanceGroup).where(AttendanceGroup.group_id == payload.group_id))
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    group.late_threshold_min = payload.late_threshold_min
    group.early_threshold_min = payload.early_threshold_min
    db.commit()
    write_log(db, "INFO", "rule_update", f"更新分组 {payload.group_id} 阈值")
    return {"message": "规则已更新"}


@app.post("/api/events/handle")
def handle_event(
    payload: EventHandleRequest,
    _: ClientUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    event = db.get(AbnormalEvent, payload.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    event.handled = True
    event.remark = payload.remark
    db.commit()
    return {"message": "已处理"}


@app.post("/api/query")
def query_attendance(
    payload: QueryRequest,
    _: ClientUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(
        select(AttendanceRecord).where(
            AttendanceRecord.group_id == payload.group_id,
            AttendanceRecord.punch_time >= datetime.fromisoformat(payload.start_date),
            AttendanceRecord.punch_time < datetime.fromisoformat(payload.end_date) + timedelta(days=1),
        )
    ).all()
    abnormal = db.scalars(
        select(AbnormalEvent).where(
            AbnormalEvent.event_date >= payload.start_date,
            AbnormalEvent.event_date <= payload.end_date,
        )
    ).all()
    return {
        "records": [
            {
                "oa_user_id": r.oa_user_id,
                "punch_time": r.punch_time.isoformat(),
                "punch_type": r.punch_type,
                "status": r.status,
                "group_id": r.group_id,
            }
            for r in rows
        ],
        "abnormal_events": [
            {
                "id": e.id,
                "oa_user_id": e.oa_user_id,
                "event_date": e.event_date,
                "event_type": e.event_type,
                "duration_min": e.duration_min,
                "detail": e.detail,
                "handled": e.handled,
            }
            for e in abnormal
        ],
    }


def sync_job() -> None:
    with Session(engine) as db:
        import asyncio

        asyncio.run(do_sync(db))


def _upsert_employees(db: Session, payload: list[dict]) -> None:
    for item in payload:
        oa_user_id = str(item.get("user_id", "")).strip()
        if not oa_user_id:
            continue
        emp = db.scalar(select(Employee).where(Employee.oa_user_id == oa_user_id))
        if not emp:
            emp = Employee(oa_user_id=oa_user_id, name=item.get("name", ""))
            db.add(emp)

        emp.name = item.get("name", emp.name)
        emp.department = item.get("department", "")
        emp.title = item.get("title", "")
        emp.group_id = item.get("group_id", "")
        emp.status = item.get("status", "active")
        emp.contact_encrypted = encrypt_text(item.get("mobile", "")) if item.get("mobile") else ""
        emp.updated_at = datetime.utcnow()


def _upsert_groups(db: Session, payload: list[dict]) -> None:
    for item in payload:
        gid = str(item.get("group_id", "")).strip()
        if not gid:
            continue
        grp = db.scalar(select(AttendanceGroup).where(AttendanceGroup.group_id == gid))
        if not grp:
            grp = AttendanceGroup(group_id=gid, group_name=item.get("group_name", gid))
            db.add(grp)

        grp.group_name = item.get("group_name", grp.group_name)
        grp.on_duty_time = item.get("on_duty_time", grp.on_duty_time)
        grp.off_duty_time = item.get("off_duty_time", grp.off_duty_time)


def _insert_records(db: Session, records: list[dict]) -> None:
    for rec in records:
        rec_id = str(rec.get("record_id", "")).strip()
        user_id = str(rec.get("user_id", "")).strip()
        punch_time = rec.get("punch_time")
        if not rec_id or not user_id or not punch_time:
            continue
        exists = db.scalar(select(AttendanceRecord).where(AttendanceRecord.oa_record_id == rec_id))
        if exists:
            continue
        db.add(
            AttendanceRecord(
                oa_record_id=rec_id,
                oa_user_id=user_id,
                punch_time=datetime.fromisoformat(punch_time),
                punch_type=rec.get("punch_type", "on_duty"),
                status=rec.get("status", "normal"),
                group_id=rec.get("group_id", ""),
            )
        )


def _insert_abnormal_events(db: Session, grp: AttendanceGroup, events: list[AbnormalEvent]) -> None:
    del grp
    for event in events:
        dup = db.scalar(
            select(AbnormalEvent).where(
                AbnormalEvent.oa_user_id == event.oa_user_id,
                AbnormalEvent.event_date == event.event_date,
                AbnormalEvent.event_type == event.event_type,
            )
        )
        if not dup:
            db.add(event)


async def do_sync(db: Session) -> None:
    """服务端全量同步并执行异常判定。"""
    try:
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=3)

        # 先同步分组/人员，再同步打卡记录
        groups_payload = await oa_client.sync_groups()
        _upsert_groups(db, groups_payload)

        employee_payload = await oa_client.sync_employees()
        _upsert_employees(db, employee_payload)

        records_payload = await oa_client.sync_records(to_iso(date_from), to_iso(date_to))
        _insert_records(db, records_payload)
        db.commit()

        groups = db.scalars(select(AttendanceGroup)).all()
        for grp in groups:
            grp_records = db.scalars(
                select(AttendanceRecord).where(
                    AttendanceRecord.group_id == grp.group_id,
                    AttendanceRecord.punch_time >= date_from,
                    AttendanceRecord.punch_time <= date_to,
                )
            ).all()
            events = build_abnormal_events(grp_records, grp)
            _insert_abnormal_events(db, grp, events)
        db.commit()
        write_log(db, "INFO", "sync", "同步完成")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        write_log(db, "ERROR", "sync", f"同步失败: {exc}")
