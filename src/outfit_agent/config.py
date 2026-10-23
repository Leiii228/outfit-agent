"""讀取並檢查 .env 設定。"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# repo 根目錄（src/outfit_agent/config.py 往上兩層）
REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = ("DISCORD_TOKEN", "CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR")


@dataclass(frozen=True)
class Config:
    discord_token: str
    channel_id: int
    claude_model: str
    data_dir: Path


def load_config() -> Config:
    """從 repo 根目錄的 .env 讀設定；少一項或格式不對就印出錯誤並結束程式。"""
    load_dotenv(REPO_ROOT / ".env")

    missing = [key for key in REQUIRED_KEYS if not os.getenv(key, "").strip()]
    if missing:
        sys.exit(
            f"[設定錯誤] .env 缺少：{', '.join(missing)}\n"
            f"請在 {REPO_ROOT / '.env'} 補上（範本見 .env.example）。"
        )

    channel_id = os.environ["CHANNEL_ID"].strip()
    if not channel_id.isdigit():
        sys.exit("[設定錯誤] CHANNEL_ID 應該是一串數字。")

    return Config(
        discord_token=os.environ["DISCORD_TOKEN"].strip(),
        channel_id=int(channel_id),
        claude_model=os.environ["CLAUDE_MODEL"].strip(),
        data_dir=Path(os.environ["DATA_DIR"].strip()).expanduser().resolve(),
    )
