# Discord Bot 設定步驟

> 這份文件教你：
> 1. 在 Discord Developer Portal 新建一個**全新的** bot（不要沿用之前食物 agent 的 bot）
> 2. 打開 Message Content Intent
> 3. 拿到 bot token，存進 `.env`
> 4. 設定 bot 需要的權限，把它邀進你自己的 Server
>
> Discord Developer Portal（開發者後台）**只有英文介面**，所以下面寫的按鈕名稱都是網頁上看到的英文。

---

## ⚠️ 先看這裡：bot token 是密碼

bot token 等於這個 bot 的**帳號＋密碼**。拿到它的人可以冒充你的 bot，在你的 Server 裡用 bot 的權限做任何事，例如狂發訊息、讀取頻道內容。

- ❌ **絕對不能**貼給任何人，包括同學、老師、助教。
- ❌ **絕對不能**貼進 Claude Code 的對話裡。需要設定時，你自己打開 `.env` 貼上就好，**不要叫 Claude 幫你填**。
- ❌ **絕對不能** commit 進 git，也不能 push 到 GitHub。`.env` 已經列在 `.gitignore` 裡了，**只要 token 只放在 `.env`，就不會被 commit**。
- ❌ 不要截圖、不要貼在 LINE、Discord、筆記軟體或任何雲端文件。
- ✅ 只放在電腦上這個專案的 `.env` 檔案裡。

**萬一不小心外流了**：馬上照第三節的步驟按 **Reset Token** 換一組新的，舊的會立刻失效，再把新的貼進 `.env`。

---

## 一、新建 application 和 bot

application（應用程式）是你在 Discord 開發者後台建立的一個「專案」，bot 是掛在這個專案底下、會出現在 Server 裡的那個機器人帳號。

1. 用瀏覽器打開 <https://discord.com/developers/applications>。
2. 如果要求登入，就用你平常的 Discord 帳號登入。
3. 你會看到「**Applications**」頁面，之前做食物 agent 的 application 可能也在這裡，**不要點它**。
4. 點**右上角**藍色的「**New Application**」按鈕。
5. 跳出小視窗：
   1. 「**NAME**」欄輸入新名字，例如 `穿搭紀錄 bot`。
   2. 勾選下面那個「同意 Discord 開發者服務條款」的方框。
   3. 點「**Create**」。
   4. 如果出現「我不是機器人」驗證，照指示完成。
6. 進到這個新 application 的「**General Information**」頁面。確認**頁面左上角**顯示的是剛剛取的新名字，不是食物 agent 的名字。
7. 點**左邊選單**的「**Bot**」。
8. 在這一頁可以：
   - 「**USERNAME**」：改 bot 在 Discord 裡顯示的名字，例如 `穿搭紀錄`。
   - 「**ICON**」：上傳 bot 的頭像（不一定要做）。
   - 有改的話，點畫面下方跳出的綠色「**Save Changes**」。

### 把 bot 設成「只有你能邀請」（建議）

預設任何拿到邀請連結的人，都能把你的 bot 邀進他們的 Server。改成私人會比較安全，要先做 A 再做 B，順序反了會出現錯誤訊息。

A. 先關掉預設的安裝連結：

1. 點左邊選單的「**Installation**」。
2. 找到「**Install Link**」這一區，把下拉選單改成「**None**」。
3. 點下方的「**Save Changes**」。

B. 再關掉 Public Bot：

1. 點左邊選單的「**Bot**」。
2. 在「**Authorization Flow**」這一區，找到「**PUBLIC BOT**」，把開關**關掉**，變成灰色。
3. 點下方的「**Save Changes**」。

---

## 二、打開 Message Content Intent（一定要做）

1. 確認你在左邊選單的「**Bot**」頁面。
2. 往下捲到「**Privileged Gateway Intents**」這一區，裡面有三個開關：
   - PRESENCE INTENT：**不用開**
   - SERVER MEMBERS INTENT：**不用開**
   - **MESSAGE CONTENT INTENT**：**打開**，變成藍色
3. 點畫面下方跳出的「**Save Changes**」。

### 為什麼一定要開？

Intent 是「bot 向 Discord 申請要收到哪些資料」的開關。Discord 為了保護隱私，**預設不會把訊息的內容給 bot**，包括：

- 訊息的文字：沒開的話，bot 看不到別人打的 `!紀錄`、`!統計`、`!冷宮`，指令全部沒反應。
- 訊息的**附件**：沒開的話，bot 收到的訊息裡附件是空的，**看不到上傳的照片**，整個穿搭紀錄功能都不會動。

不開的話，bot 只知道「有人在頻道傳了東西」，但不知道傳了什麼。所以這個 agent 一定要打開它。

---

## 三、拿到 bot token

1. 確認你在左邊選單的「**Bot**」頁面。
2. 在上方「**TOKEN**」這一區，點「**Reset Token**」。
   - 新建的 bot 也是按這個按鈕來產生 token。
3. 跳出確認視窗，點「**Yes, do it!**」。
4. 如果你的 Discord 帳號有開兩步驟驗證，這裡會要求輸入驗證碼或密碼，照指示輸入。
5. 畫面上會出現一長串英文和數字，旁邊有「**Copy**」按鈕。
   - ⚠️ **這串 token 只會顯示這一次**，離開頁面就看不到了。如果忘了複製，只能再按一次 Reset Token 重新產生。
6. 點「**Copy**」，然後**馬上**照第五節的步驟把它貼進 `.env`。
   - 不要先貼到記事本暫存再另外存檔，也不要貼到任何其他地方。

---

## 四、設定權限並把 bot 邀進你的 Server

這個 agent 需要以下 5 個權限：

| 權限（網頁上的英文名稱） | 中文 | 為什麼需要 |
|---|---|---|
| **View Channels** | 檢視頻道 | 看得到 #穿搭紀錄、讀得到裡面的訊息。這就是「讀訊息」權限 |
| **Send Messages** | 傳送訊息 | 回覆上傳者、回覆指令、發每週提醒 |
| **Add Reactions** | 新增反應 | 對照片訊息加 ⏳ |
| **Attach Files** | 附加檔案 | `!統計` 要傳長條圖 |
| **Read Message History** | 讀取訊息歷史 | 用「回覆該則訊息」的方式回答時需要 |

不需要給「**Administrator**」（管理員）或其他權限，給越少越安全。

### 步驟

1. 點左邊選單的「**OAuth2**」。
2. 往下捲到「**OAuth2 URL Generator**」這一區。
3. 在「**SCOPES**」的一大排勾選框裡，**只勾**「**bot**」。
4. 勾完後，下面會多出一區「**BOT PERMISSIONS**」，分成 GENERAL / TEXT / VOICE 三欄。照下面勾這 5 個，**其他都不要勾**：
   - GENERAL PERMISSIONS 欄：**View Channels**
   - TEXT PERMISSIONS 欄：**Send Messages**、**Attach Files**、**Read Message History**、**Add Reactions**
5. 再往下捲：
   - 如果有「**INTEGRATION TYPE**」下拉選單，選「**Guild Install**」。
   - 最下面的「**GENERATED URL**」有一條很長的網址，點右邊的「**Copy**」。
   - 檢查方法：這條網址裡應該有 `permissions=101440`，這個數字就代表剛好勾了這 5 個權限。
6. 在瀏覽器**開一個新分頁**，貼上剛剛的網址，按 Enter。
7. 出現 Discord 的授權畫面：
   1. 「**新增至伺服器**」（ADD TO SERVER）的下拉選單，選**你自己的 Server**。
      - 只有你有「管理伺服器」權限的 Server 才會出現在這裡。你是 Server 擁有者，一定會出現。
   2. 點「**繼續**」（Continue）。
   3. 下一頁會列出剛剛那 5 個權限，確認都有勾，點「**授權**」（Authorize）。
   4. 如果出現「我不是機器人」驗證，照指示完成。
8. 看到「已授權」（Authorized）就成功了，這個分頁可以關掉。

### 確認 bot 已經進來

1. 回到 Discord，打開你的 Server。
2. 點右上角的「**人形**」圖示（顯示成員名單）。
3. 成員名單裡應該會看到你的 bot，名字旁邊有 **APP**（或 BOT）標籤。
4. 現在它會顯示「**離線**」，這是正常的。等之後 agent 程式跑起來，它才會變成上線。

> 如果你把 # 穿搭紀錄 設成了**私人頻道**，還要多做一步：
> 在 # 穿搭紀錄 上按右鍵 → 「**編輯頻道**」（Edit Channel）→「**權限**」（Permissions）→「**新增成員或身分組**」（Add members or roles）→ 搜尋你的 bot 名字並加入。
> 不是私人頻道的話，這一步不用做。

---

## 五、把 token 和 CHANNEL_ID 存進 .env

`.env` 是放在專案資料夾裡的設定檔，agent 啟動時會從這裡讀取設定。

1. 按鍵盤的 **Windows 鍵**，輸入 `記事本`（或 `Notepad`），按 Enter 打開記事本。
2. 在記事本裡輸入下面四行，`=` 後面換成你自己的值：

   ```
   DISCORD_TOKEN=這裡貼上第三節複製的 token
   CHANNEL_ID=這裡貼上 discord-server-setup.md 拿到的頻道 ID
   CLAUDE_MODEL=claude-sonnet-5-5
   DATA_DIR=C:\Users\User\outfit-data
   ```

   - `=` 前後**不要有空格**，值也**不要加引號**。
   - `DISCORD_TOKEN=` 後面：按 **Ctrl + V** 貼上剛剛複製的 token。
   - `DATA_DIR` 是照片和 Excel 要存放的資料夾，建議用上面這個在專案外面的位置，資料夾之後 agent 會自動建立。
3. 點左上角「**檔案**」→「**另存新檔**」。
4. 在存檔視窗裡：
   1. 上方路徑切換到專案資料夾 `C:\Users\User\outfit-agent`。
   2. 「**存檔類型**」改成「**所有檔案 (\*.\*)**」。⚠️ 這步很重要，不改的話會存成 `.env.txt`，agent 讀不到。
   3. 「**檔案名稱**」輸入 `.env`。
   4. 「**編碼**」選 **UTF-8**。
   5. 點「**存檔**」。
5. 關掉記事本。

### 確認 .env 不會被 commit

你可以在 Claude Code 裡說：「請確認 `.env` 存在，而且有被 `.gitignore` 忽略，**不要讀取內容**。」Claude 只會檢查檔案在不在、有沒有被 git 忽略，不會看到 token。

---

## 完成檢查

- [ ] Developer Portal 裡有一個**新的** application，不是食物 agent 那個
- [ ] Bot 頁面的 **MESSAGE CONTENT INTENT** 是打開的
- [ ] 你的 Server 成員名單裡看得到這個 bot（顯示離線）
- [ ] 專案資料夾 `C:\Users\User\outfit-agent` 裡有 `.env`，不是 `.env.txt`
- [ ] token 只存在 `.env` 裡，沒有貼到任何其他地方，也沒有貼進對話
