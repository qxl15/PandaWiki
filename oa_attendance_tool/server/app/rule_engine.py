"""考勤异常判定引擎（服务端执行）。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .models import AbnormalEvent, AttendanceGroup, AttendanceRecord


def _hm_to_minutes(hm: str) -> int:
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def _ts_to_minutes(ts: datetime) -> int:
    return ts.hour * 60 + ts.minute


def build_abnormal_events(records: list[AttendanceRecord], group: AttendanceGroup) -> list[AbnormalEvent]:
    """按分组规则计算迟到/早退/缺卡。

    说明：
    - 所有规则计算在服务端执行。
    - 客户端仅消费结果。
    """
    user_day = defaultdict(list)
    for item in records:
        key = (item.oa_user_id, item.punch_time.strftime("%Y-%m-%d"))
        user_day[key].append(item)

    abnormal_events: list[AbnormalEvent] = []
    on_duty_min = _hm_to_minutes(group.on_duty_time)
    off_duty_min = _hm_to_minutes(group.off_duty_time)

    for (oa_user_id, event_date), day_records in user_day.items():
        day_records.sort(key=lambda x: x.punch_time)
        first = day_records[0]
        last = day_records[-1]

        late_min = _ts_to_minutes(first.punch_time) - on_duty_min
        if late_min > group.late_threshold_min:
            abnormal_events.append(
                AbnormalEvent(
                    oa_user_id=oa_user_id,
                    event_date=event_date,
                    event_type="late",
                    duration_min=late_min,
                    detail=f"迟到 {late_min} 分钟",
                )
            )

        early_min = off_duty_min - _ts_to_minutes(last.punch_time)
        if early_min > group.early_threshold_min:
            abnormal_events.append(
                AbnormalEvent(
                    oa_user_id=oa_user_id,
                    event_date=event_date,
                    event_type="early_leave",
                    duration_min=early_min,
                    detail=f"早退 {early_min} 分钟",
                )
            )

        if group.missing_card_enabled and len(day_records) < 2:
            abnormal_events.append(
                AbnormalEvent(
                    oa_user_id=oa_user_id,
                    event_date=event_date,
                    event_type="missing_card",
                    duration_min=0,
                    detail="疑似缺卡（当天打卡次数不足2次）",
                )
            )

    return abnormal_events
