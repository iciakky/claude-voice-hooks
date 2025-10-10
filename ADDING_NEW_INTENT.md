# How to Add a New Intent

Thanks to the **Intent Enum + Directory-Driven Architecture**, managing audio feedback is now completely code-free!

## Quick Guide

### Adding a New Intent (Requires Code)

Edit `claude_intent_hook.py` and add a new enum member:

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
    # ✨ NEW: Add new intent
    THINKING = IntentMetadata(
        description_zh="正在執行長時間思考或處理任務"
    )
```

Then create the audio directory:
```bash
mkdir audio/thinking
cp your_thinking_sound.wav audio/thinking/
```

---

## 🎵 Managing Audio Files (Zero Code Changes!)

### Adding Audio Variants

**No code changes needed!** Just add files to the intent directory:

```bash
# Add new variant for completion intent
cp excited_completion.wav audio/completion/

# Add multiple variants
cp calm.wav audio/completion/
cp professional.wav audio/completion/
cp energetic.wav audio/completion/

# Supports .wav and .mp3
cp new_sound.mp3 audio/failure/
```

The system will **automatically discover and randomly select** from all audio files!

### Current Audio Structure

```
audio/
├── completion/          # 8 variants
│   ├── completion.wav
│   ├── completion1.wav
│   ├── completion2.wav
│   └── ... (randomly selected)
├── failure/             # 5 variants
│   ├── failure.wav
│   ├── failure1.wav
│   └── ...
├── authorization/       # 18 variants!
│   ├── authorization.wav
│   ├── authorization1.wav
│   └── ...
└── fallback.wav         # Global fallback
```

### Removing Audio Variants

```bash
# Temporary disable (rename)
mv audio/completion/annoying.wav audio/completion/annoying.wav.disabled

# Permanent removal
rm audio/completion/old_sound.wav

# Move to backup
mkdir audio/completion/_backup
mv audio/completion/test*.wav audio/completion/_backup/
```

---

## 🎯 How It Works

### Discovery Process

1. **Directory Scan**: System scans `audio/{intent}/` for `.wav` and `.mp3` files
2. **Random Selection**: Each playback randomly picks from available files
3. **Fallback**: If directory empty → uses `audio/fallback.wav`

### Example Workflow

```python
# Code never changes!
await play_intent_audio(Intent.COMPLETION)

# What happens:
# 1. Scan audio/completion/ → [completion.wav, completion1.wav, ...]
# 2. Random choice → completion3.wav
# 3. Play: audio/completion/completion3.wav
```

---

## ✅ Benefits

### Zero-Code Audio Management
- ✅ **Add variants**: Just copy files to directory
- ✅ **Remove variants**: Just delete files
- ✅ **Test new sounds**: Drag & drop, restart hook
- ✅ **A/B testing**: Add/remove without touching code

### Semantic File Names
```bash
# Before: completion-1.wav, completion-2.wav (unclear)
# After:
audio/completion/
├── excited.wav
├── calm.wav
├── professional.wav
└── energetic.wav
```

### Natural Organization
- Each intent has its own folder
- Easy to see available variants
- No file name conflicts
- Simple backup/restore

---

## 🔧 Advanced Usage

### Intent-Specific Moods

Organize by context:
```bash
audio/completion/
├── daytime-professional.wav
├── daytime-casual.wav
├── nighttime-quiet.wav
└── weekend-fun.wav
```

### Temporary Testing

```bash
# Test new sound (no commit)
cp experimental.wav audio/completion/test.wav

# Remove if not good
rm audio/completion/test.wav
```

### Batch Operations

```bash
# Add multiple sounds at once
cp sounds/completion/*.wav audio/completion/

# Archive old sounds
tar -czf old_sounds.tar.gz audio/completion/*
mv audio/completion/* audio/_archive/
```

---

## 🚨 Validation

### Startup Checks

The system validates on startup:

1. **Each intent has files OR fallback.wav exists**
2. **Warns if intent directory empty** (will use fallback)
3. **Fails if fallback missing when needed**

### Example Output

```
Audio configuration warnings:
  - thinking: No audio files in thinking/ (will use fallback.wav)

[OK] Validation passed!
```

---

## 📊 Architecture Benefits

| Task | Before (Hardcoded) | After (Directory-Driven) |
|------|-------------------|--------------------------|
| **Add variant** | Edit code ❌ | Copy file ✅ |
| **Remove variant** | Edit code ❌ | Delete file ✅ |
| **Test sound** | Edit code ❌ | Drag & drop ✅ |
| **See variants** | Read code | `ls audio/intent/` ✅ |
| **Backup audio** | Manual select | `cp -r audio/intent/` ✅ |

---

## 🎵 File Format Support

Supported formats:
- `.wav` - Recommended (universal compatibility)
- `.mp3` - Supported

The system automatically discovers both formats in intent directories.

---

## 💡 Tips

1. **Use descriptive names**: `excited.wav` better than `1.wav`
2. **Keep fallback.wav**: Required if any intent has no audio
3. **Test locally**: Add new sounds, restart hook, verify random selection
4. **Version control**: Consider `.gitignore` for test sounds

---

## Example: Complete Workflow

```bash
# 1. Create new intent (code change - one time)
# Add THINKING to Intent enum in claude_intent_hook.py

# 2. Create directory
mkdir audio/thinking

# 3. Add audio files (no code changes!)
cp thinking_sound1.wav audio/thinking/
cp thinking_sound2.wav audio/thinking/
cp processing.mp3 audio/thinking/

# 4. Done! System auto-discovers:
# - thinking_sound1.wav
# - thinking_sound2.wav
# - processing.mp3

# 5. Add more variants anytime (still no code!)
cp new_thinking.wav audio/thinking/
```

🎉 **Audio management is now a runtime concern, not a code concern!**
