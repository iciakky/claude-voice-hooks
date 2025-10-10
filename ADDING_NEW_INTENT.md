# How to Add a New Intent

Thanks to the **Intent Enum pattern**, adding a new intent requires changing **only ONE location**.

## Quick Guide

### Adding "thinking" Intent

**Single Change Required:**

Edit `claude_intent_hook.py` and add a new enum member to the `Intent` class:

```python
class Intent(Enum):
    """Intent types with embedded configuration."""

    COMPLETION = IntentMetadata(
        audio_file="completion.wav",
        description_zh="工作已完成，詢問使用者下一步要做什麼"
    )
    FAILURE = IntentMetadata(
        audio_file="failure.wav",
        description_zh="作業失敗或遇到錯誤，請求使用者協助"
    )
    AUTHORIZATION = IntentMetadata(
        audio_file="authorization.wav",
        description_zh="工作進行中，等待使用者授權或選擇選項"
    )
    # ✨ NEW: Add this single entry
    THINKING = IntentMetadata(
        audio_file="thinking.wav",
        description_zh="正在執行長時間思考或處理任務"
    )
```

**Physical Asset:**
Create `audio/thinking.wav` file

**That's it!** Everything else auto-updates:
- ✅ Classification prompt regenerated from enum iteration
- ✅ Validation logic includes new intent automatically
- ✅ Audio file mapping auto-derived
- ✅ Startup validation checks new file
- ✅ Type safety enforced by enum

## What Gets Auto-Updated

| Component | How It Updates |
|-----------|----------------|
| **Type Hints** | `Intent` enum includes new member |
| **Classification Prompt** | `build_classification_prompt()` iterates `Intent` enum |
| **Validation Logic** | `VALID_INTENTS` derived from enum iteration |
| **Audio Mapping** | `AUDIO_FILES` derived from enum iteration |
| **Startup Checks** | `validate_audio_files()` iterates enum |

## Benefits of Enum Pattern

### ✅ Single Source of Truth
- **One place to add intent**: Just the enum definition
- **Zero duplication**: No separate lists or mappings to maintain
- **Impossible to desync**: Configuration embedded in enum

### ✅ Type Safety
- **Compile-time checks**: Can't pass invalid intent
- **IDE autocomplete**: `Intent.COMPLETION` shows all options
- **Refactoring safety**: Rename Intent.COMPLETION → IDE updates all usages

### ✅ Fail-Fast Behavior
- **Startup validation**: Missing audio file → immediate error
- **Runtime safety**: Type system prevents invalid values
- **Clear error messages**: Exactly which file is missing

### ✅ Developer Experience
```python
# Before (string-based)
await play_intent_audio("completion")  # Typo risk: "completoin"

# After (enum-based)
await play_intent_audio(Intent.COMPLETION)  # IDE autocomplete, no typos possible
```

## Comparison: Before vs After

### Before (List Registry Pattern)
```
To add "thinking" intent:
1. Add to INTENT_REGISTRY list
2. Update IntentType Literal

Risk: Forget step 2 → runtime errors
```

### After (Enum Pattern)
```
To add "thinking" intent:
1. Add Intent.THINKING enum member

Risk: None - everything auto-derived!
```

## Advanced: Customizing Intent Behavior

If you need per-intent custom behavior:

```python
class Intent(Enum):
    COMPLETION = IntentMetadata(...)

    @property
    def needs_user_input(self) -> bool:
        """Some intents require user interaction."""
        return self in {Intent.AUTHORIZATION, Intent.FAILURE}

    @property
    def stabilization_delay(self) -> float:
        """Different intents may need different delays."""
        delays = {
            Intent.COMPLETION: 1.0,
            Intent.THINKING: 2.0,  # Longer audio
        }
        return delays.get(self, 1.0)
```

All extension points remain within the single `Intent` enum definition!
