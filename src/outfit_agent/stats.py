"""個人統計（docs/architecture.md 第 9、10、11、12 節）。所有函式都只做計算，不碰檔案。"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import COLORS, TYPES, Item
from .storage import Record

COLD_DAYS = 14


def outfits_of(records: list[Record], user_id: str) -> list[Record]:
    """只留下這個人「是穿搭」的紀錄，依時間由舊到新排。"""
    mine = [r for r in records if r.user_id == user_id and r.is_outfit]
    return sorted(mine, key=lambda r: r.when)


def all_items(outfits: list[Record]) -> list[Item]:
    return [item for r in outfits for item in r.items]


def color_counts(items: list[Item]) -> list[tuple[str, int]]:
    """每件單品的顏色各算一次；依次數由多到少，一樣多時依固定顏色順序。"""
    counts = Counter(i.color for i in items)
    return sorted(counts.items(), key=lambda kv: (-kv[1], COLORS.index(kv[0])))


def top_colors(items: list[Item], n: int = 3) -> list[tuple[str, int]]:
    return color_counts(items)[:n]


def type_counts(items: list[Item]) -> list[tuple[str, int]]:
    counts = Counter(i.type for i in items)
    return [(t, counts[t]) for t in TYPES if counts[t]]


def main_color(items: tuple[Item, ...]) -> str:
    """這套裡件數最多的顏色；一樣多時取上衣的顏色，沒有上衣就依固定顏色順序。"""
    counts = Counter(i.color for i in items)
    best = max(counts.values())
    tied = [c for c in counts if counts[c] == best]
    if len(tied) == 1:
        return tied[0]
    for item in items:
        if item.type == "上衣" and item.color in tied:
            return item.color
    return min(tied, key=COLORS.index)


@dataclass(frozen=True)
class Repeat:
    times: int  # 第 N 次穿（含這次）
    days_ago: int  # 上次是幾天前


def repeat_info(past: list[Record], items: tuple[Item, ...], now: datetime) -> dict[tuple[str, str], Repeat]:
    """對這次的每件單品，找這個人以前有沒有「類型＋顏色」相同的。沒穿過的不會出現在結果裡。"""
    result = {}
    for key in {i.key for i in items}:
        hits = [r for r in past if any(i.key == key for i in r.items)]
        if hits:
            last = max(r.when for r in hits)
            result[key] = Repeat(times=len(hits) + 1, days_ago=(now.date() - last.date()).days)
    return result


def recent(outfits: list[Record], n: int = 5) -> list[Record]:
    return sorted(outfits, key=lambda r: r.when, reverse=True)[:n]


def cold_items(outfits: list[Record], now: datetime, days: int = COLD_DAYS) -> list[tuple[str, str, int]]:
    """超過 days 天沒穿的「類型＋顏色」，回傳 (類型, 顏色, 幾天前)，依天數由多到少。"""
    last_worn: dict[tuple[str, str], datetime] = {}
    for r in outfits:
        for item in r.items:
            if item.key not in last_worn or r.when > last_worn[item.key]:
                last_worn[item.key] = r.when
    cold = []
    for (t, c), when in last_worn.items():
        ago = (now.date() - when.date()).days
        if ago > days:
            cold.append((t, c, ago))
    return sorted(cold, key=lambda x: (-x[2], TYPES.index(x[0]), COLORS.index(x[1])))


def latest_names(records: list[Record]) -> dict[str, str]:
    """每個 user id 最近一次上傳時的顯示名稱。"""
    names: dict[str, tuple[datetime, str]] = {}
    for r in records:
        if r.user_id not in names or r.when >= names[r.user_id][0]:
            names[r.user_id] = (r.when, r.name)
    return {uid: name for uid, (_, name) in names.items()}


def last_week_range(now: datetime) -> tuple[datetime, datetime]:
    """上週一 00:00 到這週一 00:00（不含）。"""
    this_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return this_monday - timedelta(days=7), this_monday


@dataclass(frozen=True)
class WeeklyLine:
    name: str
    count: int
    top_color: str


def weekly_summary(records: list[Record], now: datetime) -> tuple[datetime, datetime, list[WeeklyLine]]:
    """上週每個人記錄了幾套、最常穿的顏色；依套數由多到少。上週沒人記錄時清單是空的。"""
    start, end = last_week_range(now)
    names = latest_names(records)
    by_user: dict[str, list[Record]] = {}
    for r in records:
        if r.is_outfit and start <= r.when < end:
            by_user.setdefault(r.user_id, []).append(r)
    lines = []
    for uid, outfits in by_user.items():
        top = top_colors(all_items(outfits), 1)
        lines.append(WeeklyLine(names.get(uid, "（未知）"), len(outfits), top[0][0]))
    lines.sort(key=lambda line: (-line.count, line.name))
    return start, end, lines

