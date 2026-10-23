"""共用的固定選項與資料型態。"""

from dataclasses import dataclass

# 固定選項（docs/architecture.md 第 5-2 節）；顏色順序也是統計「一樣多」時的排序依據
TYPES = ("上衣", "外套", "褲子", "裙子", "洋裝", "鞋子")
COLORS = ("黑", "白", "灰", "米", "棕", "紅", "粉", "橘", "黃", "綠", "藍", "紫", "多色")

DESC_MAX = 20
STYLE_MAX = 50
STYLE_SHORT_MAX = 10

NOT_OUTFIT = "不是穿搭"


class AnalysisError(Exception):
    """分析失敗（照片壞掉、claude -p 出錯、回傳格式不對）。訊息只印在終端機。"""


@dataclass(frozen=True)
class Item:
    type: str
    color: str
    desc: str

    @property
    def key(self) -> tuple[str, str]:
        """「類型＋顏色」相同就當成同一件。"""
        return (self.type, self.color)


@dataclass(frozen=True)
class Analysis:
    kind: str  # "outfit"、"not_outfit"、"group"（合照）
    items: tuple[Item, ...]
    style: str
    style_short: str

    @property
    def is_outfit(self) -> bool:
        return self.kind == "outfit"
