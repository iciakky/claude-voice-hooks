# Audio Setup Guide

Audio files are **not included** in version control. You need to provide your own audio files.

## Quick Setup

### 1. Create Directory Structure

```bash
mkdir -p audio/{completion,failure,authorization}
```

### 2. Add Audio Files

Place your audio files (`.wav` or `.mp3`) in the corresponding directories:

```
audio/
├── completion/
│   ├── your_sound1.wav
│   └── your_sound2.wav
├── failure/
│   └── your_sound.wav
├── authorization/
│   └── your_sound.wav
└── fallback.wav  # Required fallback sound
```

### 3. Required Files

**Minimum requirement:**
- `audio/fallback.wav` - Used when intent directories are empty

**Recommended:**
- At least one audio file in each intent directory

---

## Audio File Requirements

### Supported Formats
- `.wav` (recommended)
- `.mp3`

### Naming
- Files can have any name
- Use descriptive names: `excited.wav`, `professional.mp3`

### Multiple Variants
Place multiple files in the same directory for **random selection**:

```bash
audio/completion/
├── happy.wav
├── professional.wav
└── energetic.wav

# System will randomly pick one each time
```

---

## Where to Get Audio Files

### Option 1: Generate with Text-to-Speech
- [ElevenLabs](https://elevenlabs.io/)
- [Google Cloud TTS](https://cloud.google.com/text-to-speech)
- macOS: `say -o output.wav "Your text"`

### Option 2: Sound Libraries
- [Freesound](https://freesound.org/)
- [Zapsplat](https://www.zapsplat.com/)
- [BBC Sound Effects](https://sound-effects.bbcrewind.co.uk/)

### Option 3: Record Your Own
Use any audio recording software and export as `.wav` or `.mp3`

---

## Example Setup Script

```bash
#!/bin/bash

# Create directories
mkdir -p audio/{completion,failure,authorization}

# Generate simple beep sounds (macOS example)
say -o audio/completion/done.wav "Task completed"
say -o audio/failure/error.wav "Error occurred"
say -o audio/authorization/waiting.wav "Waiting for input"
say -o audio/fallback.wav "Notification"

echo "Audio setup complete!"
```

---

## Validation

After setup, test with:

```bash
python claude_intent_hook.py
```

The system will:
- ✅ Validate audio configuration
- ⚠️ Warn if directories are empty (will use fallback)
- ❌ Fail if fallback.wav missing when needed

---

## Troubleshooting

### "fallback.wav is required but missing"
- Create `audio/fallback.wav` with any notification sound

### "No audio files in {intent}/"
- Add at least one `.wav` or `.mp3` file to the directory
- Or rely on `fallback.wav` (warning will show but system works)

### Audio not playing
- Check file format is `.wav` or `.mp3`
- Verify file permissions
- Test file plays in media player

---

## .gitignore Configuration

Audio files are ignored by version control to:
- Keep repository lightweight
- Allow personalized audio configurations
- Prevent binary file bloat

If you want to share your audio setup with team members, consider:
- Hosting files separately (Google Drive, S3, etc.)
- Documenting your audio sources
- Creating setup scripts
