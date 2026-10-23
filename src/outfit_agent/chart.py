"""!統計 的顏色分布長條圖。每根長條塗成它代表的衣服顏色。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 不開視窗，只畫成圖檔
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

# 長條的顏色就是資料本身（衣服顏色），所以直接用接近實物的色票
SWATCH = {
    "黑": "#262626", "白": "#FFFFFF", "灰": "#9E9E9E", "米": "#D9C7A3",
    "棕": "#8B5A3C", "紅": "#D93A3A", "粉": "#F2A2B8", "橘": "#F08A2C",
    "黃": "#F2C94C", "綠": "#4C9A5A", "藍": "#3567B5", "紫": "#8257B0",
    "多色": "#E8E8E8",
}
INK = "#2B2B2B"
MUTED = "#6B6B6B"
GRID = "#E6E6E6"
OUTLINE = "#8C8C8C"  # 白色、米色、多色等淺色長條需要外框才看得到

_CJK_FONTS = ("Microsoft JhengHei", "Microsoft YaHei", "Noto Sans CJK TC", "PingFang TC")


def _pick_font() -> str | None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    return next((name for name in _CJK_FONTS if name in available), None)


def draw_color_chart(counts: list[tuple[str, int]], title: str, path: Path) -> None:
    """counts 是 [(顏色, 件數), …]，已依件數排好。畫成 PNG 存到 path。"""
    font = _pick_font()
    rc = {"font.family": font} if font else {}
    with plt.rc_context(rc):
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
        fig.patch.set_facecolor("white")
        labels = [c for c, _ in counts]
        values = [n for _, n in counts]
        bars = ax.bar(
            labels,
            values,
            width=0.62,
            color=[SWATCH[c] for c in labels],
            edgecolor=[OUTLINE if c in ("白", "米", "多色", "黃") else SWATCH[c] for c in labels],
            linewidth=1,
            zorder=2,
        )
        for bar, color in zip(bars, labels):
            if color == "多色":
                bar.set_hatch("///")
        ax.bar_label(bars, padding=3, color=INK, fontsize=10)

        ax.set_title(title, color=INK, fontsize=13, loc="left", pad=12)
        ax.set_ylabel("件數", color=MUTED, fontsize=10)
        ax.tick_params(axis="x", colors=INK, labelsize=11, length=0)
        ax.tick_params(axis="y", colors=MUTED, labelsize=9, length=0)
        ax.yaxis.get_major_locator().set_params(integer=True)
        ax.set_ylim(0, max(values) * 1.15 + 0.5)
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)

        fig.tight_layout()
        fig.savefig(path, format="png", facecolor="white")
        plt.close(fig)
