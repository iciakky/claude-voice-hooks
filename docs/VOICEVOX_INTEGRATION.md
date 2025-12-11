# VOICEVOX TTS Integration

## Overview

VOICEVOX is integrated as the TTS engine with the following advantages:

- **Zero VRAM usage**: VOICEVOX runs as external service (no GPU memory on main server)
- **Faster startup**: No model loading required (< 100ms initialization)
- **Simple API**: REST-based synthesis (no complex configuration)
- **Required service**: VOICEVOX must be running for server to start

## Architecture

```
Server Startup
    ↓
TTS Engine Factory
    ├─ Create VoicevoxEngine
    ├─ Health check (GET /version)
    └─ Success → Server ready (0 VRAM)
        (Failure → Server exits with error)

Translation+TTS Workflow
    ↓
POST /translate_and_speak
    ↓ (queue immediately, return 202)
    ↓
Translation Worker
    ├─ Translate: EN/ZH → JA (Ollama)
    └─ Enqueue to TTS queue
        ↓
    TTS Worker
        ├─ Synthesize with VOICEVOX:
        │   ├─ POST /audio_query?text={ja}&speaker=20
        │   └─ POST /synthesis (with AudioQuery JSON)
        │       → Returns binary WAV
        │
        ├─ Save to audio/tmp/tts_{id}.wav
        └─ Play audio
```

## Configuration

### config.yaml

```yaml
# VOICEVOX Configuration
voicevox:
  base_url: "http://localhost:50021"
  speaker_id: 20          # Speaker/voice ID (default: 20)
  timeout: 60.0           # HTTP timeout (seconds)

  # Voice parameters
  speed_scale: 1.0        # Speed multiplier (0.5-2.0)
  pitch_scale: 1.0        # Pitch multiplier (0.5-2.0)
  volume_scale: 1.0       # Volume multiplier (0.5-2.0)
```

### Environment Variables (optional)

```bash
# Override config file
export VOICEVOX_BASE_URL=http://localhost:50021
export VOICEVOX_SPEAKER_ID=20
```

## Installation & Setup

### 1. Install VOICEVOX

Download and install VOICEVOX from official website:
- https://voicevox.hiroshiba.jp/

Or use Docker:
```bash
docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

### 2. Start VOICEVOX Service

Launch VOICEVOX application or Docker container.

Verify service is running:
```bash
curl http://localhost:50021/version
# Expected: "0.25.0" (or similar version string)
```

### 3. Install Python Dependencies

```bash
# Add aiohttp for HTTP client
uv pip install aiohttp
```

### 4. Test VOICEVOX Engine

```bash
# Run test script
.venv\Scripts\python.exe test_voicevox_engine.py

# Expected output:
# [Test 1] Health Check
# ✓ VOICEVOX service is healthy
# [Test 2] Get Available Speakers
# Found X speakers...
# [Test 3] Synthesize Japanese Text to Bytes
# ✓ Synthesized XXXXX bytes of audio
# ...
```

### 5. Start Server

```bash
# Windows
scripts\start_server.bat

# Linux/macOS
.venv/bin/python -m uvicorn server.app:app --host 127.0.0.1 --port 8765
```

Check startup logs:
```
[INFO] Initializing Translation+TTS system...
[INFO]   VOICEVOX TTS Engine initialized
[INFO]   Speaker ID: 20
[INFO]   Base URL: http://localhost:50021
[INFO]   Translation+TTS workers started
[INFO] Server Ready - VOICEVOX Translation+TTS Active
```

## Usage

### API Endpoint (unchanged)

```bash
# Translate English → Japanese → Synthesize → Play
curl -X POST http://localhost:8765/translate_and_speak \
  -H "Content-Type: application/json" \
  -d '{"text": "The server is ready for testing", "return_audio": false}'

# Response: {"status":"queued","message":"Request queued for translation and TTS","queue_position":1}
```

### Server Logs

```
[INFO] [abc123] /translate_and_speak request: The server is ready for testing...
[INFO] [abc123] Request queued (position: 1)
[INFO] [abc123] Translation worker: translating text...
[INFO] [abc123] Translation completed: サーバーのテスト準備ができました
[INFO] [abc123] TTS worker: synthesizing audio...
[DEBUG] Generating AudioQuery for: サーバーのテスト準備ができました
[DEBUG] Synthesizing audio with speaker 20
[INFO] Synthesized 123456 bytes of audio
[INFO] [abc123] TTS completed, playing audio...
```

## Speaker Selection

### List Available Speakers

```python
from server.core.tts_voicevox import VoicevoxEngine

engine = VoicevoxEngine()
speakers = await engine.get_speakers()

for speaker in speakers:
    print(f"{speaker['name']}:")
    for style in speaker['styles']:
        print(f"  - {style['name']}: ID={style['id']}")
```

### Change Speaker

Edit `config.yaml`:
```yaml
voicevox:
  speaker_id: 20  # Change to desired speaker ID
```

Or override per-request in code:
```python
wav_bytes = await engine.synthesize(
    text="テキスト",
    speaker_id=3  # Override default speaker
)
```

## Troubleshooting

### VOICEVOX Service Not Available

**Symptom**: Server fails to start with error

```
[ERROR] Failed to initialize Translation+TTS system: ...
[ERROR] Please ensure VOICEVOX is running at http://localhost:50021
RuntimeError: Translation+TTS system initialization failed. VOICEVOX service is required.
```

**Solution**:
1. Ensure VOICEVOX is running: `curl http://localhost:50021/version`
2. Check firewall settings (port 50021)
3. Verify `config.yaml` base_url is correct
4. Restart VOICEVOX service if needed

### Synthesis Fails with HTTP 422

**Symptom**: `HTTPValidationError` when calling `/audio_query`

**Cause**: Invalid speaker_id or text format

**Solution**:
1. Verify speaker_id exists: Run test script to list speakers
2. Ensure text is Japanese (katakana/hiragana/kanji)
3. Check VOICEVOX version supports speaker_id

### Audio Quality Issues

**Symptom**: Generated audio sounds poor

**Solution**: Adjust voice parameters in `config.yaml`:
```yaml
voicevox:
  speed_scale: 1.0     # Slow down: 0.8, Speed up: 1.2
  pitch_scale: 1.0     # Lower: 0.9, Higher: 1.1
  volume_scale: 1.0    # Quieter: 0.8, Louder: 1.2
```

## Performance

### Zero VRAM on Main Server

VOICEVOX runs as external service → main server uses 0 GPU memory for TTS

**Current (VOICEVOX)**:
- Startup: ~0.5G VRAM (Ollama translation only)
- Inference: ~1.0G VRAM (Ollama only, TTS in separate VOICEVOX process)
- Synthesis Latency: ~2-3s (typical Japanese sentence)

### Key Metrics

| Metric | Value |
|--------|-------|
| VRAM Usage (Main Server) | ~0.5-1.0 GB (Ollama only) |
| VRAM Usage (VOICEVOX) | Separate process |
| Startup Time | < 100ms (engine creation) |
| Synthesis Latency | ~2-3s per sentence |
| Quality | Good (VOICEVOX preset voices) |

## Implementation Files

- `server/core/tts_voicevox.py` - VOICEVOX engine implementation
- `server/core/tts_factory.py` - TTS engine factory with fallback
- `server/app.py` - Server integration
- `config.yaml` - Configuration
- `test_voicevox_engine.py` - Test script

## Future Improvements

- [ ] Cache AudioQuery objects for repeated phrases
- [ ] Support multiple languages (if VOICEVOX adds)
- [ ] Streaming synthesis for long texts
- [ ] Voice style selection per request
- [ ] Quality/latency presets (fast vs quality)
