"""每週提醒（docs/architecture.md 第 12 節）。"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from . import stats
from .storage import Record

STATE_NAME = "state.json"
SEND_HOUR = 9


def this_week_send_time(now: datetime) -> datetime:
    """這週一 09:00（本機時間）。"""
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=SEND_HOUR, minute=0, second=0, microsecond=0)


def _load_state(data_dir: Path) -> dict:
    try:
        return json.loads((data_dir / STATE_NAME).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def already_done(data_dir: Path, now: datetime) -> bool:
    """這週的提醒是否已經處理過（發過，或檢查過上週沒人記錄）。"""
    week = this_week_send_time(now).date().isoformat()
    return _load_state(data_dir).get("last_weekly_week") == week


def mark_done(data_dir: Path, now: datetime) -> None:
    state = _load_state(data_dir)
    state["last_weekly_week"] = this_week_send_time(now).date().isoformat()
    (data_dir / STATE_NAME).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def should_catch_up(data_dir: Path, now: datetime) -> bool:
    """啟動時用：已經過了這週一 09:00、這週卻還沒處理過，就要補發。只補這一週。"""
    return now >= this_week_send_time(now) and not already_done(data_dir, now)


def build_message(records: list[Record], now: datetime) -> str | None:
    """上週摘要的訊息文字；上週沒人記錄穿搭就回傳 None（不發）。"""
    start, end, lines = stats.weekly_summary(records, now)
    if not lines:
        return None
    last_day = end - timedelta(days=1)
    out = [f"📅 上週穿搭摘要（{start.month}/{start.day}～{last_day.month}/{last_day.day}）"]
    out += [f"・{line.name}：{line.count} 套，最常穿 {line.top_color}" for line in lines]
    return "\n".join(out)
