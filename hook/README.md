# Claude Code Think Aloud Hook

Make Claude Code "speak its mind" — automatically translate and vocalize Claude's thinking.

## Features

- **Extract Thinking**: Captures the last thinking content from Claude Code transcript
- **Deduplication**: Tracks processed thinking via hash to avoid repetition
- **Async Translation+TTS**: Calls local API for non-blocking processing
- **Dual Event Triggers**: Supports both `PreToolUse` and `Stop` hook events

## How It Works

```
Claude Code (thinking)
    → Hook triggers (PreToolUse / Stop)
    → Extract last thinking content
    → Check for duplicates (MD5 hash)
    → POST /translate_and_speak
    → Translate to Japanese (Ollama)
    → TTS synthesis and playback (VOICEVOX)
```

## Setup

### 1. Ensure Server is Running

```bash
# Start the translation+TTS server
scripts\start_server.bat  # Windows
# or
.venv/bin/python -m uvicorn server.app:app --host 127.0.0.1 --port 8765  # Linux/macOS
```

Server should be running at `http://127.0.0.1:8765`.

### 2. Configure Claude Code

Copy `hook/settings.json` to your Claude Code config directory:

**Windows**:
```
%APPDATA%\Anthropic\Claude Code\settings.json
```

**macOS/Linux**:
```
~/.config/claude-code/settings.json
```

Or merge the content from `hook/settings.json` into your existing config.

### 3. Update Python Path

Check that the path in `settings.json` is correct:

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

Update to your actual path.

## Usage

Once configured, the hook triggers automatically:

1. **PreToolUse**: Before Claude uses a tool
2. **Stop**: When Claude stops waiting for user input

Each trigger will:
- Translate new thinking content to Japanese
- Speak it aloud via TTS

## State File

The hook uses this file to track state:

```
hook/.last_thinking_hash
```

Stores the MD5 hash of the last processed thinking for deduplication. File is auto-created and gitignored.

## Error Handling

All errors are output to **stderr**, including:

- Transcript parsing errors
- API connection errors (with HTTP status and response)
- File I/O errors

Example error output:

```
[think_aloud_hook ERROR] HTTP error: 422
[think_aloud_hook ERROR] Response: {"detail":"Validation error"}
```

## Configuration

**API URL**: `http://127.0.0.1:8765/translate_and_speak`
**Timeout**: 5 seconds (configurable in `settings.json`)
**State file**: `hook/.last_thinking_hash`

## Troubleshooting

### Hook Not Executing

1. Verify Claude Code loaded `settings.json`
2. Run `claude --debug` to see hook execution logs
3. Check Python path is correct

### API Connection Failed

```
[think_aloud_hook ERROR] URL error: Connection refused
```

**Solution**: Ensure server is running (`scripts\start_server.bat`)

### No Thinking Extracted

**Reason**: Claude's response may not contain thinking blocks

**Verify**: Manually check transcript file for thinking content

## Development

### Main Functions

Edit `think_aloud_hook.py`:

- `extract_thinking_from_record()`: Extract thinking from JSON
- `get_last_thinking()`: Traverse transcript for last thinking
- `call_translation_tts_api()`: Call API

### Adding Features

Extend `main()` with additional logic:
- Filter specific thinking types
- Add more deduplication conditions
- Customize API parameters

## Files

- **think_aloud_hook.py**: Main hook script
- **settings.json**: Claude Code hook configuration
- **.last_thinking_hash**: State file (auto-generated, gitignored)
