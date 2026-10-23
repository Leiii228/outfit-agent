"""Discord 機器人本體：收訊息、⏳、排隊、指令、回覆、每週提醒排程。"""

import asyncio
import os
import tempfile
import traceback
from dataclasses import dataclass
from datetime import datetime
from datetime import time as dtime
from pathlib import Path

import discord
from discord.ext import tasks
from discord.utils import escape_markdown

from . import chart, stats, weekly
from .analyzer import MAX_UPLOAD_BYTES, analyze, prepare_image
from .config import Config
from .models import AnalysisError, Analysis
from .storage import (
    EXCEL_RETRY_SECONDS,
    Record,
    append_record_with_retry,
    ensure_dirs,
    read_records,
    save_photo,
)

HOURGLASS = "⏳"
FAIL_TEXT = "分析失敗，請再傳一次"
NO_RECORD_TEXT = "你還沒有紀錄"
READ_BUSY_TEXT = "紀錄檔暫時讀不到（可能正被 Excel 開著），請稍後再試"
ERROR_TEXT = "發生錯誤，請稍後再試"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
DISCORD_MAX_LEN = 2000

LOCAL_TZ = datetime.now().astimezone().tzinfo


def local_now() -> datetime:
    return datetime.now().replace(microsecond=0)


def _esc(text: str) -> str:
    """別人送進來或 claude 產生的文字放進 Discord 訊息前，先跳脫 markdown 符號。"""
    return escape_markdown(text)


# 常見的打法差異：「記錄」和「紀錄」、簡體字
COMMAND_ALIASES = {
    "!記錄": "!紀錄", "!纪录": "!紀錄", "!记录": "!紀錄",
    "!统计": "!統計",
    "!冷宫": "!冷宮",
    "!测试提醒": "!測試提醒", "!測試提示": "!測試提醒",
}


def _parse_command(content: str) -> str:
    """取出指令名稱。全形「！」當成半形「!」，驚嘆號後面多打的空格也忽略。
    只取第一個詞，後面接的文字直接丟掉。"""
    text = content.strip()
    if not text or text[0] not in "!！":
        return ""
    rest = text[1:].split(maxsplit=1)
    word = "!" + rest[0] if rest else "!"
    return COMMAND_ALIASES.get(word, word)


def _is_image(att: discord.Attachment) -> bool:
    return (att.content_type or "").startswith("image/") or Path(att.filename).suffix.lower() in IMAGE_EXTS


def _days_text(days: int) -> str:
    return "上次是今天稍早" if days == 0 else f"上次是 {days} 天前"


def _top_text(tops: list[tuple[str, int]]) -> str:
    return "、".join(f"{c}（{n} 件）" for c, n in tops)


@dataclass
class Job:
    message: discord.Message
    attachment: discord.Attachment
    is_last: bool  # 這則訊息的最後一張；處理完就拿掉 ⏳


class OutfitBot(discord.Client):
    def __init__(self, cfg: Config):
        intents = discord.Intents.default()
        intents.message_content = True  # 要看得到訊息文字和附件
        super().__init__(
            intents=intents,
            # 機器人所有發言都不會觸發 @everyone / @身分組 / @某人，只保留「回覆時通知上傳者本人」
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False, replied_user=True
            ),
        )
        self.cfg = cfg
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self._caught_up = False
        self.commands = {
            "!紀錄": self.cmd_history,
            "!統計": self.cmd_stats,
            "!冷宮": self.cmd_cold,
            "!測試提醒": self.cmd_test_weekly,
        }

    # ---------- 啟動 ----------

    async def setup_hook(self) -> None:
        ensure_dirs(self.cfg.data_dir)
        asyncio.create_task(self._worker())
        self.weekly_loop.start()

    async def on_ready(self) -> None:
        print(f"✓ 已連上 Discord：{self.user}（只聽頻道 {self.cfg.channel_id}）")
        print(f"  DATA_DIR：{self.cfg.data_dir}")
        if self.get_channel(self.cfg.channel_id) is None:
            print("⚠ 找不到 CHANNEL_ID 指定的頻道：請確認編號正確、bot 已被邀進 Server 並看得到這個頻道")
        if not self._caught_up:
            self._caught_up = True
            if weekly.should_catch_up(self.cfg.data_dir, local_now()):
                print("… 這週一 09:00 的每週提醒還沒處理，現在補發")
                await self.run_weekly(mark=True)

    # ---------- 收訊息 ----------

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id != self.cfg.channel_id or message.author.bot:
            return

        # 指令只看第一個詞，後面接的文字直接丟掉，不會拿去用
        command = _parse_command(message.content)
        if command in self.commands:
            print(f"> {message.author} 打了 {command}")
            try:
                await self.commands[command](message)
            except PermissionError:
                await self._reply(message, READ_BUSY_TEXT)
            except Exception:
                traceback.print_exc()
                await self._reply(message, ERROR_TEXT)
            return

        images = [a for a in message.attachments if _is_image(a)]
        if not images:
            return
        try:
            await message.add_reaction(HOURGLASS)
        except discord.HTTPException as exc:
            print(f"⚠ 加 ⏳ 失敗（請確認 bot 有「新增反應」權限）：{exc}")
        for idx, att in enumerate(images):
            await self.queue.put(Job(message, att, is_last=idx == len(images) - 1))
        print(f"+ 收到 {message.author} 的 {len(images)} 張照片，排隊中（目前共 {self.queue.qsize()} 張）")

    async def _reply(self, message: discord.Message, text: str, **kwargs) -> None:
        text = text[:DISCORD_MAX_LEN]
        try:
            await message.reply(text, **kwargs)
        except discord.HTTPException:
            # 原訊息可能已被刪除，改成直接發在頻道
            try:
                await message.channel.send(text, **kwargs)
            except discord.HTTPException as exc:
                print(f"✗ 回覆失敗：{exc}")

    # ---------- 排隊處理照片（只有這一個處理員，同一時間只會跑一個 claude -p） ----------

    async def _worker(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                await self._process(job)
            except Exception:
                traceback.print_exc()
                await self._reply(job.message, FAIL_TEXT)
            finally:
                if job.is_last:
                    try:
                        await job.message.remove_reaction(HOURGLASS, self.user)
                    except discord.HTTPException:
                        pass
                self.queue.task_done()

    async def _process(self, job: Job) -> None:
        msg, att = job.message, job.attachment
        when = msg.created_at.astimezone().replace(tzinfo=None, microsecond=0)
        user_id = str(msg.author.id)
        print(f"… 分析 {msg.author} 的照片 {att.filename!r}")

        try:
            if att.size > MAX_UPLOAD_BYTES:
                raise AnalysisError("檔案超過 10 MB")
            jpeg = await asyncio.to_thread(prepare_image, await att.read())
            analysis = await analyze(jpeg, self.cfg.claude_model)
            photo = await asyncio.to_thread(
                save_photo, self.cfg.data_dir, jpeg, when, analysis.style_short
            )
        except AnalysisError as exc:
            print(f"✗ 分析失敗：{exc}")
            await self._reply(msg, FAIL_TEXT)
            return

        records = await self._read_records_with_retry()
        past = stats.outfits_of(records, user_id)

        if analysis.is_outfit:
            total = len(past) + 1
            record = Record(
                when=when,
                name=msg.author.display_name,
                user_id=user_id,
                items=analysis.items,
                main_color=stats.main_color(analysis.items),
                style=analysis.style,
                total=total,
                photo=photo,
            )
            repeats = stats.repeat_info(past, analysis.items, when)
            tops = stats.top_colors(stats.all_items(past) + list(analysis.items))
            reply = self._outfit_reply(analysis, repeats, total, tops)
        else:
            total = len(past)
            record = Record(
                when=when,
                name=msg.author.display_name,
                user_id=user_id,
                items=None,
                main_color="",
                style=analysis.style,
                total=total,
                photo=photo,
            )
            reply = self._not_outfit_reply(analysis, total)

        await append_record_with_retry(self.cfg.data_dir, record)
        await self._reply(msg, reply)
        print(f"✓ 已記錄：{photo}")

    @staticmethod
    def _outfit_reply(
        analysis: Analysis,
        repeats: dict[tuple[str, str], stats.Repeat],
        total: int,
        tops: list[tuple[str, int]],
    ) -> str:
        lines = ["✅ 已記錄你的穿搭！", "", "👕 單品"]
        for item in analysis.items:
            rep = repeats.get(item.key)
            note = f"第 {rep.times} 次穿，{_days_text(rep.days_ago)}" if rep else "第一次記錄"
            desc = f"：{_esc(item.desc)}" if item.desc else ""
            lines.append(f"・{item.type}／{item.color}{desc}（{note}）")
        lines += [
            "",
            f"🎨 風格：{_esc(analysis.style)}",
            "",
            f"📊 你目前共有 {total} 套穿搭",
            f"🏆 最常穿的顏色：{_top_text(tops)}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _not_outfit_reply(analysis: Analysis, total: int) -> str:
        lines = [f"🔍 這張看起來是「{_esc(analysis.style)}」，不算進穿搭統計喔。"]
        if analysis.kind == "group":
            lines.append("合照不會記進統計，請傳只有你自己的照片。")
        lines.append(f"你目前共有 {total} 套穿搭紀錄。")
        return "\n".join(lines)

    async def _read_records_with_retry(self) -> list[Record]:
        attempt = 0
        while True:
            try:
                return await asyncio.to_thread(read_records, self.cfg.data_dir)
            except PermissionError:
                attempt += 1
                print(f"⚠ outfits.xlsx 讀不到（可能正被 Excel 開著），{EXCEL_RETRY_SECONDS} 秒後重試（第 {attempt} 次）")
                await asyncio.sleep(EXCEL_RETRY_SECONDS)

    # ---------- 指令（只回覆打指令那個人自己的資料） ----------

    async def _my_outfits(self, message: discord.Message) -> list[Record] | None:
        records = await asyncio.to_thread(read_records, self.cfg.data_dir)
        mine = stats.outfits_of(records, str(message.author.id))
        if not mine:
            await self._reply(message, NO_RECORD_TEXT)
            return None
        return mine

    async def cmd_history(self, message: discord.Message) -> None:
        mine = await self._my_outfits(message)
        if mine is None:
            return
        latest = stats.recent(mine, 5)
        lines = [f"你最近 {len(latest)} 筆穿搭："]
        for idx, r in enumerate(latest, start=1):
            items = "、".join(f"{i.type}/{i.color}" for i in r.items)
            lines.append(f"{idx}. {r.when:%Y-%m-%d}　{items}")
        await self._reply(message, "\n".join(lines))

    async def cmd_stats(self, message: discord.Message) -> None:
        mine = await self._my_outfits(message)
        if mine is None:
            return
        items = stats.all_items(mine)
        types = "、".join(f"{t} {n}" for t, n in stats.type_counts(items))
        text = f"你目前共有 {len(mine)} 套穿搭\n各類型件數：{types}"

        # 圖檔放在系統暫存資料夾，傳出去後（不管成功與否）馬上刪掉
        fd, tmp = tempfile.mkstemp(prefix="outfit-chart-", suffix=".png")
        os.close(fd)
        try:
            await asyncio.to_thread(
                chart.draw_color_chart,
                stats.color_counts(items),
                "你的顏色分布（每件單品各算一次）",
                Path(tmp),
            )
            await self._reply(message, text, file=discord.File(tmp, filename="colors.png"))
        finally:
            try:
                os.remove(tmp)
            except OSError as exc:
                print(f"⚠ 暫存圖檔刪除失敗：{exc}")

    async def cmd_cold(self, message: discord.Message) -> None:
        mine = await self._my_outfits(message)
        if mine is None:
            return
        cold = stats.cold_items(mine, local_now())
        if not cold:
            await self._reply(message, "目前沒有打入冷宮的單品 👍")
            return
        lines = [f"這些單品超過 {stats.COLD_DAYS} 天沒穿了："]
        lines += [f"・{t}/{c}　上次是 {days} 天前" for t, c, days in cold]
        await self._reply(message, "\n".join(lines))

    async def cmd_test_weekly(self, message: discord.Message) -> None:
        """測試用：馬上跑一次每週提醒，不會記成「這週已發」。"""
        sent = await self.run_weekly(mark=False)
        if sent is None:
            await self._reply(message, ERROR_TEXT)
        elif not sent:
            await self._reply(message, "（測試）上週沒有人記錄穿搭，所以每週提醒不會發。")

    # ---------- 每週提醒 ----------

    @tasks.loop(time=dtime(hour=weekly.SEND_HOUR, tzinfo=LOCAL_TZ))
    async def weekly_loop(self) -> None:
        now = local_now()
        if now.weekday() == 0 and not weekly.already_done(self.cfg.data_dir, now):
            await self.run_weekly(mark=True)

    @weekly_loop.before_loop
    async def _before_weekly(self) -> None:
        await self.wait_until_ready()

    async def run_weekly(self, mark: bool) -> bool | None:
        """發上週摘要；上週沒人記錄就不發。回傳有沒有發出去；出錯回傳 None。"""
        try:
            now = local_now()
            records = await self._read_records_with_retry()
            text = weekly.build_message(records, now)
            sent = False
            if text:
                channel = self.get_channel(self.cfg.channel_id) or await self.fetch_channel(
                    self.cfg.channel_id
                )
                await channel.send(_esc(text))
                sent = True
                print("✓ 已發出每週提醒" + ("" if mark else "（測試）"))
            else:
                print("… 上週沒有人記錄穿搭，每週提醒不發")
            if mark:
                weekly.mark_done(self.cfg.data_dir, now)
            return sent
        except Exception:
            traceback.print_exc()
            return None
