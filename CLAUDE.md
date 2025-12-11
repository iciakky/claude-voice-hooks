# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Translation + TTS server that translates English/Chinese text to Japanese and synthesizes speech using VOICEVOX. The system uses a triple-queue async architecture for non-blocking request processing.

**Core workflow**: Client → Translation (Ollama) → TTS (VOICEVOX) → Audio Playback → Done

## Essential Commands

### Setup and Installation

```bash
# Create virtual environment and install dependencies (uses uv package manager)
uv venv .venv
uv pip install -r requirements_py313.txt

# Install Ollama translation model (required)
ollama create my-translator -f my-translator.modelfile

# Install VOICEVOX (required external service)
# Download from https://voicevox.hiroshiba.jp/ or use Docker:
docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest

# Verify VOICEVOX is running
curl http://localhost:50021/version
```

### Running the Server

```bash
# Windows
scripts\start_server.bat

# Linux/macOS
.venv/bin/python -m uvicorn server.app:app --host 127.0.0.1 --port 8765

# Server runs on http://127.0.0.1:8765
# API docs auto-generated at http://127.0.0.1:8765/docs
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_app.py

# Run with verbose output
pytest -v

# Translation + TTS integration test
curl -X POST http://localhost:8765/translate_and_speak \
  -H "Content-Type: application/json" \
  -d '{"text": "The server is ready for testing", "return_audio": false}'
```

### Development

```bash
# Install dependencies (use uv, not pip)
uv pip install <package>

# Update requirements
uv pip freeze > requirements_py313.txt

# Test server import (quick validation)
.venv/Scripts/python.exe -c "from server.app import app; print('✓ Import successful')"
```

## Architecture

### Triple-Queue Async System

**Core concept**: Three independent async queues enable maximum parallelism—translation, TTS synthesis, and audio playback all run concurrently without blocking each other.

```
POST /translate_and_speak → Returns 202 immediately
    ↓
[Translation Queue] → TranslationWorker
    ↓ (Ollama: EN/ZH → JA, ~0.43s)
    ↓
[TTS Queue] → TTSWorker
    ↓ (VOICEVOX: JA → WAV, ~2-3s)
    ↓
[Audio Play Queue] → AudioPlayWorker
    ↓ (System audio player, ~6s)
    ↓
Delete temporary file → Done
```

**Key file**: `server/core/translation_tts_worker.py`
- `TranslationTTSWorkerSystem` manages all three queues
- Three background workers run concurrently via `asyncio.create_task()`
- TTS semaphore limits concurrency to 1 (prevents VRAM overload)
- Statistics tracked in `self.stats` dict

### Translation Pipeline

**Key file**: `server/core/translation.py`

Translation uses custom Ollama model `my-translator` (based on qwen3:4b-instruct):
- Model defined in `my-translator.modelfile`
- Custom SYSTEM prompt for concise Japanese summaries (no thinking output)
- Performance: ~0.43s avg, 100% clean outputs
- Post-processing: `postprocess_for_tts()` optimizes text for speech:
  - Fractions: "1/2" → "1分の2"
  - Decimals: "3.2" → "3てん2"
  - Percents: "50%" → "50パーセント"
  - Removes spaces between English/numbers and Japanese
  - Converts long acronyms: "HTTP" → "Http"

### TTS Engine (VOICEVOX)

**Key file**: `server/core/tts_voicevox.py`

VOICEVOX is a **required external service** (server exits if unavailable):
- Two-step synthesis:
  1. `POST /audio_query?text={text}&speaker={speaker_id}` → AudioQuery JSON
  2. `POST /synthesis?speaker={speaker_id}` with AudioQuery → WAV bytes
- Default speaker_id: 20 (configured in `config.yaml`)
- Zero VRAM usage on main server (runs as separate process)
- Timeout: 60s (configurable)

**Key file**: `server/core/tts_factory.py`
- `create_tts_engine_with_health_check()` validates VOICEVOX availability on startup
- Health check: `GET /version` → fails startup if unreachable

### FastAPI Application

**Key file**: `server/app.py`

Endpoints:
- `POST /translate_and_speak` - Main endpoint, returns 202 Accepted immediately
- `GET /health` - Queue statistics (translation_queue_size, tts_queue_size, stats)
- `GET /` - API info

Lifespan manager:
- Startup: Load config → Initialize VOICEVOX → Start triple-queue workers
- Shutdown: Stop workers (10s timeout) → Cleanup VOICEVOX session

Global state (initialized in lifespan):
- `_config`: Server configuration
- `_tts_engine`: VoicevoxEngine instance
- `_translation_tts_worker`: TranslationTTSWorkerSystem instance

### Configuration

**Key file**: `config.yaml`

```yaml
voicevox:
  base_url: "http://localhost:50021"
  speaker_id: 20          # Default speaker
  timeout: 60.0           # HTTP timeout
  speed_scale: 1.0        # Speed multiplier
  pitch_scale: 1.0        # Pitch multiplier
  volume_scale: 1.0       # Volume multiplier
```

Environment variable overrides (optional):
- `OLLAMA_BASE_URL` - Ollama service URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Override translation model (default: my-translator)

## Important Implementation Details

### Async/Await Patterns

All I/O operations use asyncio to prevent blocking:
- Translation: `ollama.AsyncClient.chat()` (non-blocking HTTP)
- TTS: `aiohttp.ClientSession` (async HTTP to VOICEVOX)
- Audio playback: `asyncio.create_subprocess_exec()` (async process spawn)

Workers use 1-second timeout loops to allow graceful shutdown:
```python
req = await asyncio.wait_for(self.queue.get(), timeout=1.0)
```

### TTS Concurrency Control

**Critical**: TTS worker uses semaphore to limit concurrency to 1:
```python
self._tts_semaphore = asyncio.Semaphore(1)  # Only 1 TTS task at a time
async with self._tts_semaphore:
    await self.tts_engine.synthesize_to_file(...)
```

Reason: VOICEVOX external service can't handle concurrent requests reliably.

### Audio Playback Platform Detection

**Key file**: `server/core/translation_tts_worker.py:330-353`

Platform-specific commands in `_play_audio()`:
- Windows: `powershell -Command '(New-Object Media.SoundPlayer "...").PlaySync()'`
- macOS: `afplay {audio_path}`
- Linux: `aplay {audio_path}`

### Error Handling Philosophy

**Timeouts** (expected errors):
- TTS timeouts logged concisely without stack trace (server/core/translation_tts_worker.py:256-265)
- Reason: VOICEVOX can timeout on complex text, not a code bug

**Unexpected errors**:
- Logged with full stack trace (`exc_info=True`)
- Workers never crash—errors caught and stats updated

### Request ID Tracking

All requests get unique 8-char UUID for logging:
```python
request_id = str(uuid.uuid4())[:8]  # e.g., "a3f2c8b1"
```

Flows through all three queues for end-to-end traceability:
```
[a3f2c8b1] /translate_and_speak request: The server is ready...
[a3f2c8b1] Translating: The server is ready...
[a3f2c8b1] Translation result: サーバーのテスト準備ができました
[a3f2c8b1] Synthesizing TTS: サーバーのテスト準備ができました
[a3f2c8b1] Audio generated: tts_a3f2c8b1.wav
[a3f2c8b1] Playing audio: tts_a3f2c8b1.wav
```

## Package Management

**Use `uv`, not `pip`**:
- Virtual environment: `uv venv .venv`
- Install packages: `uv pip install <package>`
- Freeze dependencies: `uv pip freeze > requirements_py313.txt`

PyTorch requires custom index for CUDA builds (configured in `pyproject.toml`):
```toml
[tool.uv]
index-url = "https://download.pytorch.org/whl/cu118"
```

## Common Issues

### VOICEVOX Service Not Available

Server **will not start** if VOICEVOX is unreachable. Error message:
```
[ERROR] Failed to initialize Translation+TTS system: ...
[ERROR] Please ensure VOICEVOX is running at http://localhost:50021
RuntimeError: Translation+TTS system initialization failed. VOICEVOX service is required.
```

**Solution**: Start VOICEVOX before starting server:
```bash
# Check VOICEVOX
curl http://localhost:50021/version

# If not running, start it (or use Docker as shown in Setup)
```

### Import Errors After Cleanup

If server import fails with `ModuleNotFoundError`, check dependencies:
```bash
# Install missing package using uv
uv pip install <missing-package>

# Verify server imports
.venv/Scripts/python.exe -c "from server.app import app; print('✓ Import successful')"
```

### Audio Not Playing

Check platform-specific player is installed:
- Windows: PowerShell (built-in)
- macOS: `afplay` (built-in)
- Linux: Install `aplay` (usually in `alsa-utils` package)

## Key Files Reference

**Server Core**:
- `server/app.py` - FastAPI application with endpoints and lifespan management
- `server/models.py` - Pydantic request/response models
- `server/config.py` - Configuration loading and validation

**Translation + TTS Pipeline**:
- `server/core/translation.py` - Ollama translation with post-processing
- `server/core/tts_voicevox.py` - VOICEVOX engine client
- `server/core/tts_factory.py` - TTS engine factory with health check
- `server/core/translation_tts_worker.py` - Triple-queue worker system

**Configuration**:
- `config.yaml` - VOICEVOX configuration
- `my-translator.modelfile` - Custom Ollama translation model definition
- `pyproject.toml` - Package dependencies and uv configuration

**Documentation**:
- `README.md` - User-facing Chinese documentation (OBSOLETE: describes removed Phase 2 intent classification)
- `VOICEVOX_INTEGRATION.md` - VOICEVOX TTS integration guide (accurate)

## Testing Philosophy

Tests validate:
- Configuration loading (`tests/test_config.py`)
- API endpoints (`tests/test_app.py`)
- Integration flows (`tests/test_integration.py`)
- Performance metrics (`tests/test_performance.py`)

Run tests before commits:
```bash
pytest  # All tests must pass
```
