# CLAUDE.md

這個專案是一個跑在本機的 Discord 穿搭紀錄 agent：使用者在指定頻道上傳穿搭照片，agent 用 claude -p 分析單品與風格，存照片、寫進 Excel，並回覆個人統計。

## 開始工作前

- 開始任何工作前，先讀 `docs/architecture.md`，所有實作都要照這份文件做；需求來源在 `docs/requirements.md`。

## 安全防護

- 四段防護要各自包成一段，用清楚的註解標出開始和結束，例如：

  ```python
  # ==== 防護 1：claude -p 的檔案範圍隔離　開始 ====
  ...
  # ==== 防護 1 結束 ====
  ```

  - 防護 1：claude -p 的檔案範圍隔離（只在放單張照片的暫存資料夾執行、限制工具）
  - 防護 2：上傳者文字只當資料（不接進給 claude -p 的指示）
  - 防護 3：檢查 claude -p 的結果與清洗檔名
  - 防護 4：Excel 公式注入（開頭 = + - @ 的文字改成純文字）
- 四段防護一開始全部開啟。

## 不可以 commit 的東西

- 不可以把 `.env` commit 進 git（裡面有 DISCORD_TOKEN）。
- DATA_DIR 裡的照片、Excel 紀錄和 state.json 也不要 commit。
