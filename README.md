# Claude Voice Hooks

Translate Claude Code output to Japanese and speak it aloud.

## Quick Start

### 1. Install Dependencies

```bash
# Python environment and packages
uv venv .venv
uv pip install -r requirements_py313.txt

# Ollama - Install from https://ollama.com/
ollama create my-translator -f my-translator.modelfile

# VOICEVOX - Download and launch from https://voicevox.hiroshiba.jp/
```

### 2. Start Server

```bash
# Windows
scripts\start_server.bat

# Linux/macOS
.venv/bin/python -m uvicorn server.app:app --host 127.0.0.1 --port 8765
```

### 3. Configure Claude Code Hook

Copy `hook/settings.json` to your Claude Code config directory:

**Windows**: `%APPDATA%\Anthropic\Claude Code\settings.json`
**macOS/Linux**: `~/.config/claude-code/settings.json`

Update the path in the config:
```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{
        "command": "python /path/to/claude-voice-hooks/hook/think_aloud_hook.py"
      }]
    }]
  }
}
```

### 4. Test

**API Test**:
```bash
curl -X POST http://localhost:8765/translate_and_speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, the server is ready"}'
```

**Hook Test**: Use Claude Code normally. You should hear Japanese speech when Claude thinks.

## How It Works

```
Claude Code Thinking
    → Hook triggers (PreToolUse/Stop)
    → Extract thinking content
    → POST /translate_and_speak
    → Ollama Translation (~0.4s)
    → VOICEVOX Synthesis (~2-3s)
    → Audio Playback (automatic)
```

Three async queues run in parallel without blocking each other.

## Configuration

**config.yaml**:
```yaml
voicevox:
  base_url: "http://localhost:50021"
  speaker_id: 20        # Voice character
  timeout: 60.0
```

**Environment variables** (optional):
- `OLLAMA_BASE_URL` - Ollama service URL
- `OLLAMA_MODEL` - Translation model name

## Troubleshooting

**Server won't start**:
```bash
# Check VOICEVOX is running
curl http://localhost:50021/version
```

**Translation model not found**:
```bash
# Recreate the model
ollama create my-translator -f my-translator.modelfile
```

**Hook not working**:
- Verify server is running at `http://127.0.0.1:8765`
- Check Python path in `settings.json` is correct
- Run `claude --debug` to see hook execution logs

**Audio playback fails**:
- Windows: Ensure PowerShell is available
- macOS: Ensure `afplay` is available (built-in)
- Linux: Install `aplay` (`sudo apt install alsa-utils`)

## API Documentation

After starting the server, visit: http://localhost:8765/docs

## License

MIT License
