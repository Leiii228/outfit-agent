"""程式入口：讀設定、連上 Discord。

四段安全防護都在 src/outfit_agent/guards.py（行號見 README.md「安全防護」一節）。
"""

import sys

import discord

from .bot import OutfitBot
from .config import load_config


def main() -> None:
    # 終端機編碼印不出的字（例如 emoji）用 ? 代替，不讓 print 讓程式當掉；每印一行就馬上顯示
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace", line_buffering=True)
    cfg = load_config()
    bot = OutfitBot(cfg)
    try:
        bot.run(cfg.discord_token)
    except discord.LoginFailure:
        sys.exit("[設定錯誤] DISCORD_TOKEN 不正確，請到 Discord Developer Portal 重設 token 後更新 .env。")
    except discord.PrivilegedIntentsRequired:
        sys.exit(
            "[設定錯誤] 沒有打開 Message Content Intent。"
            "請到 Discord Developer Portal → Bot → Privileged Gateway Intents 打開後再啟動。"
        )


if __name__ == "__main__":
    main()
