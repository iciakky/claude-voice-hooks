# Claude Code 語音意圖提示 Hook

當 Claude Code 停下來等待使用者回應時，自動分析意圖並播放對應的音效提示。

> ⚠️ **重要提醒：本專案不包含音效檔案**
> Clone 後必須自行準備音效檔案才能運行。最低需求：`audio/fallback.wav`
> 詳見「快速開始」第 3 步驟。

## 功能特性

- ✅ **自動意圖分類**：使用本地 Gemma-3n-E4B-it 模型分析 Claude 的訊息
- ✅ **三種意圖類型**：
  - `completion` - 工作完成詢問下一步
  - `failure` - 作業失敗請求協助
  - `authorization` - 工作途中等待使用者授權或選擇
- ✅ **多音檔隨機選擇**：每個 intent 可配置多個音效，隨機播放增加變化性
- ✅ **目錄驅動架構**：新增音檔無需修改程式碼，直接放入對應目錄即可
- ✅ **靈活音檔格式**：支援 `.wav` 和 `.mp3` 格式
- ✅ **效能優化**：僅提取訊息關鍵行進行分類，提升本地模型速度
- ✅ **非同步執行**：音效播放不會阻塞 Claude Code
- ✅ **跨平台支援**：Windows、macOS、Linux

## 系統需求

1. **Python 3.7+**
2. **Ollama** 與 **gemma3n:e4b** 模型
3. **音效檔案**（**必須自行準備**，參見 [AUDIO_SETUP.md](AUDIO_SETUP.md)）
   - 最低需求：`audio/fallback.wav`
   - 建議：為每個 intent 目錄新增音效

⚠️ **注意：專案不包含音效檔案，clone 後必須自行準備才能運行。**

## ⚡ 新使用者檢查清單

Clone 後必須完成的步驟：

**前置需求：**
- [ ] Python 3.7+ 已安裝
- [ ] Ollama 已安裝並運行
- [ ] 已下載 gemma3n:e4b 模型（`ollama pull gemma3n:e4b`）

**設定步驟：**
- [ ] 從 `settings.json.template` 建立 `settings.json`
- [ ] 替換 `settings.json` 中的專案路徑
- [ ] **建立 `audio/fallback.wav`**（必要！）
- [ ] （可選）為各 intent 目錄新增音效

**驗證：**
- [ ] 執行 `python claude_intent_hook.py` 無錯誤

❌ 如果看到 "fallback.wav is required but missing" → 請先完成音效準備
✅ 看到 "Audio file validation passed" → 可以開始使用！

---

## 快速開始

### 1. 安裝 Ollama 與模型

```bash
# 安裝 Ollama (參考 https://ollama.ai)
# Windows: 下載安裝程式
# macOS: brew install ollama
# Linux: curl https://ollama.ai/install.sh | sh

# 下載 Gemma 模型
ollama pull gemma3n:e4b
```

### 2. 配置 Claude Code Hook

**初次設定：**

```bash
# 從範本建立個人化設定檔
cp settings.json.template settings.json

# 編輯 settings.json，替換路徑為您的專案實際路徑
# Windows 範例: python C:\Users\YourName\Projects\claude-voice-hooks\claude_intent_hook.py
# macOS/Linux 範例: python /home/username/projects/claude-voice-hooks/claude_intent_hook.py
```

**專案本地 Hook：**
- 編輯後的 `settings.json` 會被 Claude Code 自動載入
- 此檔案已加入 `.gitignore`，不會進入版控

**全域 Hook（可選）：**
如果要在所有專案啟用，可將配置複製到：
- Windows: `%USERPROFILE%\.claude\settings.json`
- macOS/Linux: `~/.claude/settings.json`

### 3. 準備音效檔案（必要步驟）

⚠️ **重要：此專案不包含音效檔案，您必須自行準備。**

**最低需求（必須完成）：**

建立 `audio/fallback.wav` 作為備用音效：

```bash
# 選項 1: 使用系統 TTS 產生（macOS）
say -o audio/fallback.wav "通知"

# 選項 2: 使用系統 TTS（Linux with espeak）
espeak "notification" --stdout > audio/fallback.wav

# 選項 3: 從其他來源複製任何 .wav 或 .mp3 檔案
cp your-sound.wav audio/fallback.wav
```

**為什麼需要 fallback.wav？**
- 當 intent 目錄（completion/failure/authorization）為空時，系統會使用此檔案
- 這是唯一的必要檔案，沒有它將無法運行

**建議配置（可選但推薦）：**

為每個 intent 目錄新增音效以獲得更好的體驗：

```bash
# 新增多個 completion 音效變化
cp done1.wav audio/completion/
cp done2.wav audio/completion/
cp excited.mp3 audio/completion/

# 新增 failure 音效
cp error.wav audio/failure/
cp oops.wav audio/failure/

# 新增 authorization 音效
cp waiting.wav audio/authorization/
cp thinking.mp3 audio/authorization/
```

**音效檔案目錄結構：**

```
audio/
├── completion/          # 工作完成音效（可放多個）
│   ├── done1.wav
│   ├── done2.wav
│   └── excited.mp3
├── failure/             # 失敗/錯誤音效（可放多個）
│   ├── error1.wav
│   └── oops.wav
├── authorization/       # 等待授權音效（可放多個）
│   ├── waiting1.wav
│   ├── waiting2.wav
│   └── thinking.mp3
└── fallback.wav         # 備用音效（必要）
```

**重要說明：**
- 每個 intent 目錄可放置**多個音檔**，系統會隨機選擇播放
- 支援 `.wav` 和 `.mp3` 格式
- 如果某個 intent 目錄為空，會播放 `fallback.wav`
- **音效檔案不在版控中**，每個使用者需自行準備

📖 **詳細設定指南：** 請參閱 [AUDIO_SETUP.md](AUDIO_SETUP.md)

### 4. 驗證設定

```bash
# 驗證配置（需先完成步驟 3）
python claude_intent_hook.py

# 成功輸出（所有 intent 都有音效）：
# Audio file validation passed

# 成功輸出（使用 fallback 模式）：
# Audio configuration warnings:
#   - completion: No audio files in completion/ (will use fallback.wav)
#   - failure: No audio files in failure/ (will use fallback.wav)
#   - authorization: No audio files in authorization/ (will use fallback.wav)
# Audio file validation passed
# ✅ 這也是正常的！系統會對所有 intent 使用 fallback.wav

# 失敗輸出（缺少 fallback.wav）：
# Configuration error: fallback.wav is required but missing!
# ❌ 請回到步驟 3 建立 audio/fallback.wav
```

**驗證成功後：**

```bash
# 啟用 Claude Code debug 模式查看 hook 執行
claude --debug
```

## 配置說明

### 修改使用的模型

編輯 `claude_intent_hook.py` 第 18 行：

```python
OLLAMA_MODEL = "gemma3n:e4b"  # 改為您想使用的模型
```

### 新增音效檔案（零程式碼）

**直接將音檔複製到對應目錄即可**，無需修改程式碼：

```bash
# 新增 completion 音效變化
cp my-new-sound.wav audio/completion/

# 新增 failure 音效
cp error-sound.mp3 audio/failure/

# 系統會自動發現並隨機選擇播放
```

### 調整 Hook Timeout

編輯專案根目錄的 `settings.json`：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python /YOUR/PROJECT/PATH/claude_intent_hook.py",
            "timeout": 30000  // 調整此值（毫秒）
          }
        ]
      }
    ]
  }
}
```

**注意：** 請替換 `/YOUR/PROJECT/PATH/` 為您的實際專案路徑。

### 新增自訂 Intent

如果需要新增新的意圖類型（如 `thinking`、`progress` 等）：

📖 **完整教學：** 請參閱 [ADDING_NEW_INTENT.md](ADDING_NEW_INTENT.md)

## 工作原理

1. **觸發時機**：當 Claude Code 完成回應並停下來等待使用者時（Stop hook）或發送通知時（Notification hook）
2. **讀取對話**：從 transcript 讀取 Claude 最後一則訊息的**關鍵行**（首行 + 末兩行）
3. **意圖分類**：呼叫本地 Ollama 模型進行分類（`completion` / `failure` / `authorization`）
4. **音檔選擇**：從對應 intent 目錄隨機選擇一個音檔
5. **播放音效**：非同步播放音效，不阻塞 Claude Code
6. **不影響流程**：Hook 總是返回 `allow`，不影響正常運作

## 架構設計

### Intent Enum 模式

所有 intent 定義集中在 `Intent` Enum 中（單一來源設計）：

```python
class Intent(Enum):
    COMPLETION = IntentMetadata(
        description_zh="工作已完成，詢問使用者下一步要做什麼"
    )
    FAILURE = IntentMetadata(
        description_zh="作業失敗或遇到錯誤，請求使用者協助"
    )
    AUTHORIZATION = IntentMetadata(
        description_zh="工作進行中，等待使用者授權或選擇選項"
    )
```

### 目錄驅動音檔管理

音檔從檔案系統自動發現，無需硬編碼：

```python
# 自動掃描 audio/{intent}/ 目錄
intent.all_audio_files  # → [Path('audio/completion/done1.wav'), ...]

# 隨機選擇
intent.audio_file  # → "completion/done2.wav" (隨機)

# 自動 fallback
# 如果目錄為空 → "fallback.wav"
```

## 除錯

### 啟用詳細日誌

```bash
claude --debug
```

Hook 執行日誌會輸出到 `hook_debug.log`。

### 手動測試分類

```bash
# 測試 Ollama 模型
ollama run gemma3n:e4b "任務已完成，請問接下來要做什麼？"
# 預期輸出：completion
```

### 檢查音效配置

```bash
# 執行驗證
python claude_intent_hook.py

# 正常輸出：
# Audio file validation passed

# 如果有警告：
# Audio configuration warnings:
#   - completion: No audio files in completion/ (will use fallback.wav)
```

### 常見問題

**Q: Hook 沒有執行？**
- 確認 Python 路徑正確（Windows 使用完整路徑）
- 檢查 `settings.json` 語法正確
- 使用 `claude --debug` 查看錯誤訊息

**Q: 音效沒有播放？**
- 確認音效檔案存在於 `audio/{intent}/` 目錄
- 確認至少有 `audio/fallback.wav`
- Windows 用戶確認 PowerShell 可用
- Linux 用戶確認安裝了 `aplay`

**Q: Ollama 請求超時？**
- 增加 `settings.json` 中的 timeout 設定（預設 30 秒）
- 確認模型已下載：`ollama list`
- 確認 Ollama 服務正在執行

**Q: 分類結果不準確？**
- 調整 `build_classification_prompt()` 函數中的 prompt
- 更換其他模型嘗試（編輯 `OLLAMA_MODEL`）
- 手動測試模型輸出格式

**Q: 如何新增音效變化而不改程式碼？**
- 直接複製音檔到 `audio/{intent}/` 目錄即可
- 參考 [AUDIO_SETUP.md](AUDIO_SETUP.md)

## 技術細節

- **Intent Enum 模式**：單一來源設計，新增 intent 只需修改一處
- **目錄驅動架構**：音檔管理完全透過檔案系統，零程式碼變更
- **非同步設計**：使用 `asyncio` 處理 I/O 操作
- **關鍵行提取**：僅分析首行 + 末兩行，減少 70-90% token 使用
- **錯誤處理**：任何錯誤都不會阻塞 Claude Code
- **跨平台音效播放**：
  - Windows: PowerShell `Media.SoundPlayer`
  - macOS: `afplay`
  - Linux: `aplay`
- **JSONL 解析**：正確處理 Claude Code transcript 格式
- **隨機選擇**：使用 `random.choice()` 從多音檔中選取

## 相關文件

- 📖 [AUDIO_SETUP.md](AUDIO_SETUP.md) - 音效檔案設定完整指南
- 📖 [ADDING_NEW_INTENT.md](ADDING_NEW_INTENT.md) - 如何新增自訂 Intent 類型
- 📋 `settings.json.template` - Hook 配置範本（需複製為 `settings.json` 並自訂路徑）

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**專案特色：**
- 🎵 **零程式碼音檔管理** - 新增音效只需複製檔案
- 🎲 **多變化隨機播放** - 避免單調重複的音效
- 🏗️ **可擴充架構** - 輕鬆新增自訂 Intent 類型
- ⚡ **效能優化** - 關鍵行提取加速本地模型推理
