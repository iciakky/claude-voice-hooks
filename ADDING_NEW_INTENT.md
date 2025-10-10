# How to Add a New Intent

Thanks to the Intent Registry architecture, adding a new intent is now a **single-location change**.

## Example: Adding "thinking" Intent

### Before Registry (4 locations to change ❌)
1. Update `IntentType` Literal
2. Update `AUDIO_FILES` dict
3. Update classification prompt
4. Update validation logic (2 places)

### With Registry (1 location to change ✅)

**Step 1:** Add audio file to `audio/` directory
```bash
# Create or copy thinking.wav
cp thinking.wav audio/
```

**Step 2:** Add entry to `INTENT_REGISTRY` in `claude_intent_hook.py`
```python
INTENT_REGISTRY = [
    IntentConfig(
        name="completion",
        audio_file="completion.wav",
        description_zh="工作已完成，詢問使用者下一步要做什麼"
    ),
    IntentConfig(
        name="failure",
        audio_file="failure.wav",
        description_zh="作業失敗或遇到錯誤，請求使用者協助"
    ),
    IntentConfig(
        name="authorization",
        audio_file="authorization.wav",
        description_zh="工作進行中，等待使用者授權或選擇選項"
    ),
    # ✨ NEW: Just add this one entry
    IntentConfig(
        name="thinking",
        audio_file="thinking.wav",
        description_zh="正在執行長時間思考或處理任務"
    ),
]
```

**Step 3:** Update `IntentType` Literal (Python limitation)
```python
# Unfortunately, Python doesn't support dynamic Literal generation
IntentType = Literal["completion", "failure", "authorization", "thinking"]
```

**That's it!** Everything else auto-updates:
- ✅ Classification prompt regenerated
- ✅ Validation logic includes new intent
- ✅ Audio file mapping updated
- ✅ Startup validation checks new file

## What Gets Auto-Updated

| Component | How It Updates |
|-----------|----------------|
| Classification Prompt | `build_classification_prompt()` reads registry |
| Validation Logic | `VALID_INTENTS` derived from registry |
| Audio Mapping | `AUDIO_FILES` derived from registry |
| Startup Checks | `validate_audio_files()` iterates registry |

## Fail-Fast Behavior

If you forget to add the audio file, the hook will **fail immediately on startup** with a clear error:

```
Configuration error: Missing audio files for intents:
  - thinking: F:\repo\claude-voice-hooks\audio\thinking.wav
```

No silent failures or runtime surprises!
