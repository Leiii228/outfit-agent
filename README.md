# outfit-agent

跑在自己電腦上的 Discord 穿搭紀錄 agent。朋友在指定頻道上傳穿搭照片，agent 用 `claude -p` 分析單品與風格，把照片存在本機、在 Excel 加一筆紀錄，並回覆個人統計。

- 需求：[`docs/requirements.md`](docs/requirements.md)
- 架構：[`docs/architecture.md`](docs/architecture.md)
- Discord 設定：[`docs/discord-server-setup.md`](docs/discord-server-setup.md)、[`docs/discord-bot-setup.md`](docs/discord-bot-setup.md)

## 功能

- **只聽一個頻道**：用 Gateway（bot）模式連 Discord，只處理 `.env` 裡 `CHANNEL_ID` 那個頻道的訊息。
- **收到照片先加 ⏳**：表示收到、排隊中，處理完就拿掉。
- **一張一張排隊**：多張照片、多人同時上傳時依序處理，同一時間只會跑一個 `claude -p`。一則訊息有多張照片，每張各算一套。
- **用 claude -p 分析照片**：回傳固定格式的 JSON，內容包括：
  - 是不是穿搭
  - 單品清單：每件有類型、顏色、簡短描述
  - 風格描述
  - 類型只能是：上衣、外套、褲子、裙子、洋裝、鞋子
  - 顏色只能是：黑、白、灰、米、棕、紅、粉、橘、黃、綠、藍、紫、多色
- **檢查分析結果**：結果不是合法 JSON、欄位缺少、或類型／顏色不在選項裡時，回覆「分析失敗，請再傳一次」，程式不會當掉。
- **Excel 紀錄**：存在 `DATA_DIR/outfits.xlsx`，每次都在最後面加一列，不覆蓋舊資料。
  - 欄位：日期時間、上傳者名稱、上傳者 user id、單品清單、主要顏色、風格描述、這個人的穿搭總數、照片存放位置。
  - Excel 正被打開時，在終端機印出警告，每 10 秒重試一次，程式不會當掉。
- **分人處理**：所有統計都用 Discord user id 分開計算，不用暱稱。
- **對照以前的紀錄**：「類型＋顏色」相同就算同一件，回覆「這件你第 N 次穿，上次是 M 天前」。
- **照片存放**：存在 `DATA_DIR/photos/`，檔名是 `YYYY-MM-DD hh-mm-ss 風格簡稱.jpg`，同一秒撞名時在後面加 `-2`、`-3`。
- **不是穿搭的照片**（包含合照）：
  - 一樣存照片、一樣建檔、一樣回覆。
  - 單品清單欄寫「不是穿搭」，風格描述欄寫判定出來的東西，例如「一隻貓」。
  - 不算進個人統計。
- **回覆上傳者**：在頻道裡回覆那則訊息，內容包括：
  - 是不是穿搭
  - 單品清單
  - 風格描述
  - 哪幾件以前穿過
  - 這個人的穿搭總數
  - 最常穿的顏色前三名
- **指令**：只回覆打指令那個人自己的資料。
  - `!紀錄`：最近 5 筆穿搭（日期、單品）
  - `!統計`：顏色分布長條圖，加上各類型單品件數。圖檔傳出去後就刪掉。
  - `!冷宮`：超過 14 天沒穿到的單品
  - 沒有紀錄的人打指令時，回覆「你還沒有紀錄」。
  - `!測試提醒`：手動觸發一次每週提醒，測試用，不會影響正式的週一提醒。
- **每週提醒**：
  - 每週一 09:00（本機時間）在頻道發上週的摘要：每個人記錄了幾套、最常穿的顏色。
  - 上週沒人記錄就不發。
  - agent 沒開著而錯過時，下次啟動會補發這一週的提醒。
- **設定**：全部從 `.env` 讀取，包括 `DISCORD_TOKEN`、`CHANNEL_ID`、`CLAUDE_MODEL`、`DATA_DIR`。

## 安全防護

四段防護都在 [`src/outfit_agent/guards.py`](src/outfit_agent/guards.py)，每段都用「開始／結束」註解包起來，**四段全部開著**。

| 防護 | 內容 | 位置 |
|---|---|---|
| 防護 1：claude -p 的檔案範圍隔離 | 在只放這一張照片的暫存資料夾裡執行，用 `--restricted`、`--strict-mcp-config`、`--tools Read`、`--permission-mode dontAsk` 限制它能用的工具 | `guards.py` 第 32～89 行附近 |
| 防護 2：上傳者文字只當資料 | 給 claude -p 的指示是寫死的固定文字，訊息內容、暱稱、檔名都不會接進去 | `guards.py` 第 92～121 行附近 |
| 防護 3：檢查 claude -p 的結果與清洗檔名 | 嚴格檢查 JSON；檔名去掉 `\ / : * ? " < > \|`、`..`、控制字元；確認路徑在 photos 資料夾裡 | `guards.py` 第 124～223 行附近 |
| 防護 4：Excel 公式注入 | 開頭是 `= + - @` 的文字，前面加 `'` 存成純文字 | `guards.py` 第 226～244 行附近 |

另外，機器人的所有發言都關掉了 @everyone、@身分組、@某人 的通知效果。

## 安裝與啟動

需要先裝好 [uv](https://docs.astral.sh/uv/) 和 Claude Code（`claude` 指令），並且登入 Claude Code。

1. 照 `docs/discord-bot-setup.md` 建立 bot，並把 `.env` 放在專案根目錄。範本見 `.env.example`。
2. 在專案資料夾執行：

   ```
   uv run outfit-agent
   ```

   第一次執行時 uv 會自動裝好 Python 3.12 和所有套件。看到 `✓ 已連上 Discord` 就表示啟動成功了。
3. 要停止時，在終端機按 `Ctrl + C`。

## 資料存放

| 位置 | 內容 |
|---|---|
| `DATA_DIR/outfits.xlsx` | 所有紀錄。可以手動修改，但單品清單要維持「類型/顏色/描述；…」的格式 |
| `DATA_DIR/photos/` | 照片 |
| `DATA_DIR/state.json` | 記錄每週提醒發到哪一週 |

`.env` 和 DATA_DIR 都不會被 commit，已經列在 `.gitignore` 裡。DATA_DIR 建議放在專案資料夾外面。

## 程式結構

```
src/outfit_agent/
├── main.py      程式入口
├── config.py    讀並檢查 .env
├── bot.py       Discord：收訊息、⏳、排隊、指令、回覆、每週排程
├── guards.py    四段安全防護
├── analyzer.py  準備照片、呼叫 claude -p
├── models.py    固定選項與資料型態
├── storage.py   存照片、讀寫 Excel
├── stats.py     統計計算
├── chart.py     長條圖
└── weekly.py    每週提醒
```
