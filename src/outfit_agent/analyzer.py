"""準備照片、呼叫 claude -p 分析。安全相關的部分都在 guards.py。"""

import io

from PIL import Image

from . import guards
from .models import Analysis, AnalysisError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_SIDE = 1600  # 縮小大圖，省 Claude 額度


def prepare_image(data: bytes) -> bytes:
    """確認收到的真的是圖片，縮小後轉成 JPG。不是圖片就丟出 AnalysisError。"""
    if len(data) > MAX_UPLOAD_BYTES:
        raise AnalysisError("檔案超過 10 MB")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB")
            img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=90)
    except Exception as exc:  # Pillow 對壞檔會丟出各種例外
        raise AnalysisError(f"不是可讀取的圖片：{exc}") from exc
    return out.getvalue()


async def analyze(jpeg: bytes, model: str) -> Analysis:
    """分析一張照片（必須先經過 prepare_image()）。只收照片本身，不收任何使用者文字。"""
    raw = await guards.run_claude_isolated(jpeg, guards.build_prompt(), model)
    return guards.parse_result(raw)
