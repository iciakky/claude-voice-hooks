# Claude Code 語音意圖提示 Hook

當 Claude Code 停下來等待使用者回應時，自動分析意圖並播放對應的音效提示。

## 功能特性

- ✅ **自動意圖分類**：使用本地 Gemma-3n-E4B-it 模型分析 Claude 的訊息
- ✅ **三種意圖類型**：
  - `completion` - 工作完成詢問下一步
  - `failure` - 作業失敗請求協助
  - `authorization` - 工作途中等待使用者授權或選擇
- ✅ **非同步執行**：音效播放不會阻塞 Claude Code
- ✅ **跨平台支援**：Windows、macOS、Linux

## 系統需求

1. **Python 3.7+**
2. **Ollama** 與 **gemma-3n-E4B-it** 模型
3. **音效檔案**（需自行準備）

## 安裝步驟

### 1. 安裝 Ollama 與模型

```bash
# 安裝 Ollama (參考 https://ollama.ai)
# Windows: 下載安裝程式
# macOS: brew install ollama
# Linux: curl https://ollama.ai/install.sh | sh

# 下載 Gemma 模型
ollama pull gemma3n:e4b
```

### 2. 準備音效檔案

在 `audio/` 目錄下放置三個 WAV 檔案：

```
audio/
├── completion.wav      # 工作完成音效
├── failure.wav         # 失敗/錯誤音效
└── authorization.wav   # 等待授權音效
```

### 3. 配置 Claude Code Hook

專案已包含配置檔案 `.claude/settings.json`，Claude Code 會自動載入。

如果要在全域啟用，可將配置複製到：
- Windows: `%USERPROFILE%\.claude\settings.json`
- macOS/Linux: `~/.claude/settings.json`

### 4. 測試 Hook

```bash
# 驗證 Python 腳本可執行
python claude_intent_hook.py

# 啟用 Claude Code debug 模式查看 hook 執行
claude --debug
```

## 配置說明

### 修改模型

編輯 `claude_intent_hook.py` 第 12 行：

```python
OLLAMA_MODEL = "your-model-name"
```

### 修改音效檔案路徑

編輯第 13-17 行：

```python
AUDIO_FILES = {
    "completion": "your-completion-sound.wav",
    "failure": "your-failure-sound.wav",
    "authorization": "your-authorization-sound.wav"
}
```

### 調整 Timeout

編輯 `.claude/settings.json` 中的 `timeout` 值（單位：毫秒）：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python F:\\repo\\claude-voice-hooks\\claude_intent_hook.py",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

## 工作原理

1. **觸發時機**：當 Claude Code 完成回應並停下來等待使用者時（Stop hook）
2. **讀取對話**：從 transcript 讀取 Claude 最後一則訊息
3. **意圖分類**：呼叫本地 Ollama 模型進行分類
4. **播放音效**：根據分類結果非同步播放對應音效
5. **不阻塞流程**：Hook 總是返回 `allow`，不影響 Claude Code 正常運作

## 除錯

### 啟用詳細日誌

```bash
claude --debug
```

### 手動測試分類

```bash
# 測試 Ollama 模型
ollama run gemma-3n-E4B-it "測試訊息"
```

### 檢查 Hook 狀態

在 Claude Code 中執行：
```
/hooks
```

### 常見問題

**Q: Hook 沒有執行？**
- 確認 Python 路徑正確（Windows 使用完整路徑）
- 檢查 `.claude/settings.json` 語法正確
- 使用 `claude --debug` 查看錯誤訊息

**Q: 音效沒有播放？**
- 確認音效檔案存在於 `audio/` 目錄
- Windows 用戶確認 PowerShell 可用
- Linux 用戶確認安裝了 `aplay`

**Q: Ollama 請求超時？**
- 增加 timeout 設定（預設 30 秒）
- 確認模型已下載：`ollama list`
- 確認 Ollama 服務正在執行

**Q: 分類結果不準確？**
- 調整 `classify_intent()` 函數中的 prompt
- 更換其他模型嘗試
- 手動測試模型輸出格式

## 技術細節

- **非同步設計**：使用 `asyncio` 處理 I/O 操作
- **錯誤處理**：任何錯誤都不會阻塞 Claude Code
- **跨平台音效播放**：
  - Windows: PowerShell `Media.SoundPlayer`
  - macOS: `afplay`
  - Linux: `aplay`
- **JSONL 解析**：正確處理 Claude Code transcript 格式

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！
