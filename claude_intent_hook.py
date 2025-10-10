#!/usr/bin/env python3
"""
Claude Code Intent Classification Hook
Analyzes Claude's last message to classify intent and play corresponding audio feedback.
"""

import asyncio
import json
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Configuration
OLLAMA_MODEL = "gemma3n:e4b"


@dataclass
class IntentConfig:
    """Configuration for a single intent type."""
    name: str
    audio_file: str
    description_zh: str


# Single source of truth for all intent types
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
]

# Derive all configuration from registry
AUDIO_FILES = {cfg.name: cfg.audio_file for cfg in INTENT_REGISTRY}
VALID_INTENTS = {cfg.name for cfg in INTENT_REGISTRY}
IntentType = Literal["completion", "failure", "authorization"]  # Note: Python doesn't support dynamic Literal generation


def validate_audio_files() -> None:
    """
    Validate that all configured audio files exist at startup.

    Raises:
        FileNotFoundError: If any required audio file is missing
    """
    audio_dir = Path(__file__).parent / "audio"
    missing_files = []

    for cfg in INTENT_REGISTRY:
        audio_path = audio_dir / cfg.audio_file
        if not audio_path.exists():
            missing_files.append(f"{cfg.name}: {audio_path}")

    if missing_files:
        raise FileNotFoundError(
            f"Missing audio files for intents:\n" + "\n".join(f"  - {f}" for f in missing_files)
        )


def build_classification_prompt(message: str) -> str:
    """
    Build classification prompt dynamically from INTENT_REGISTRY.

    Args:
        message: The message to classify

    Returns:
        Formatted prompt for the LLM
    """
    intent_descriptions = "\n".join(
        f"{i+1}. {cfg.name} - {cfg.description_zh}"
        for i, cfg in enumerate(INTENT_REGISTRY)
    )

    intent_list = "、".join(cfg.name for cfg in INTENT_REGISTRY)

    return f"""分析以下 AI 助手的訊息，判斷其意圖屬於以下哪一類：

{intent_descriptions}

訊息內容：
{message}

請只回答 {intent_list} 其中之一，不要有其他文字。"""


async def read_transcript(transcript_path: str) -> str:
    """Read the conversation transcript and extract Claude's last message with text content."""
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse JSONL format - each line is a JSON object
        messages = []
        for line in lines:
            if line.strip():
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON line: {e}", file=sys.stderr)
                    continue

        # Find the last assistant message that contains text content
        # (Skip tool-only messages that have no text)
        for msg in reversed(messages):
            # Role is inside the 'message' object
            message_obj = msg.get('message', {})
            if message_obj.get('role') == 'assistant':
                # Extract text content from the message
                content = message_obj.get('content', [])

                if isinstance(content, list):
                    text_parts = [
                        block.get('text', '')
                        for block in content
                        if block.get('type') == 'text'
                    ]
                    text = ' '.join(text_parts).strip()
                    if text:  # Only return if there's actual text content
                        return text
                elif isinstance(content, str) and content.strip():
                    return content

        return ""
    except Exception as e:
        print(f"Error reading transcript: {e}", file=sys.stderr)
        return ""


async def classify_intent(message: str) -> IntentType:
    """
    Use local Gemma model to classify Claude's message intent.

    Args:
        message: The message to classify

    Returns:
        Classified intent type, defaults to 'authorization' on error
    """
    prompt = build_classification_prompt(message)

    try:
        # Call Ollama API using subprocess
        process = await asyncio.create_subprocess_exec(
            'ollama', 'run', OLLAMA_MODEL, prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0
        )

        result = stdout.decode('utf-8').strip().lower()

        # Validate result using registry
        if result in VALID_INTENTS:
            return result

        # Fallback: try to extract from result
        for intent in VALID_INTENTS:
            if intent in result:
                return intent

        # Default fallback
        print(f"Unable to classify intent from: {result}", file=sys.stderr)
        return 'authorization'

    except asyncio.TimeoutError:
        print("Ollama request timed out", file=sys.stderr)
        return 'authorization'
    except Exception as e:
        print(f"Error calling Ollama: {e}", file=sys.stderr)
        return 'authorization'


async def play_audio(audio_file: str) -> None:
    """Play audio file asynchronously without blocking."""
    audio_path = Path(__file__).parent / "audio" / audio_file

    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}", file=sys.stderr)
        return

    try:
        # Use platform-specific audio player
        if sys.platform == "win32":
            # Windows: use powershell to play audio asynchronously
            cmd = [
                'powershell', '-Command',
                f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'
            ]
        elif sys.platform == "darwin":
            # macOS: use afplay
            cmd = ['afplay', str(audio_path)]
        else:
            # Linux: use aplay (ALSA) or paplay (PulseAudio)
            cmd = ['aplay', str(audio_path)]

        # Run in background without waiting
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for process to start and stabilize
        await asyncio.sleep(0.1)
        poll_result = process.poll()

        if poll_result is not None:
            print(f"Audio process exited with code: {poll_result}", file=sys.stderr)

    except Exception as e:
        print(f"Error playing audio: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


async def play_intent_audio(intent: IntentType) -> bool:
    """
    Play audio feedback for the given intent type.

    Encapsulates audio file resolution, playback orchestration, and stabilization.

    Args:
        intent: The classified intent (completion, failure, authorization)

    Returns:
        True if audio playback was initiated successfully, False otherwise
    """
    audio_file = AUDIO_FILES.get(intent)
    if not audio_file:
        print(f"No audio file configured for intent: {intent}", file=sys.stderr)
        return False

    print(f"Playing audio for intent '{intent}': {audio_file}", file=sys.stderr)
    await play_audio(audio_file)

    # Wait for audio process to stabilize
    await asyncio.sleep(1.0)

    return True


async def main():
    """Main hook execution."""
    from datetime import datetime
    trigger_log = Path(__file__).parent / "hook_triggered.log"
    debug_log = Path(__file__).parent / "hook_debug.log"

    with open(trigger_log, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Hook triggered\n")

    # Redirect stderr to debug log
    original_stderr = sys.stderr
    sys.stderr = open(debug_log, 'a', encoding='utf-8')
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Hook started at {datetime.now().isoformat()}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    # Validate configuration at startup
    try:
        validate_audio_files()
        print("Audio file validation passed", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.stderr.close()
        sys.stderr = original_stderr
        sys.exit(1)

    try:
        # Read hook input from stdin
        hook_input = json.loads(sys.stdin.read())
        print(f"Hook input: {json.dumps(hook_input, indent=2)}", file=sys.stderr)

        hook_event = hook_input.get('hook_event_name')
        print(f"Hook event: {hook_event}", file=sys.stderr)

        # Handle Notification hook: play default sound
        if hook_event == 'Notification':
            print("Notification hook detected", file=sys.stderr)
            await play_intent_audio('authorization')
            print(f"Hook completed (Notification mode)", file=sys.stderr)
            sys.stderr.close()
            sys.stderr = original_stderr
            sys.exit(0)

        # Handle Stop hook: classify intent and play corresponding sound
        transcript_path = hook_input.get('transcript_path')
        if not transcript_path:
            print("No transcript path provided for Stop hook", file=sys.stderr)
            sys.stderr.close()
            sys.stderr = original_stderr
            sys.exit(0)

        # Read Claude's last message
        last_message = await read_transcript(transcript_path)
        if not last_message:
            print("No assistant message found in transcript", file=sys.stderr)
            await play_intent_audio('authorization')
            sys.stderr.close()
            sys.stderr = original_stderr
            sys.exit(0)

        # Classify intent
        intent = await classify_intent(last_message)
        print(f"Classified intent: {intent}", file=sys.stderr)

        # Play corresponding audio
        await play_intent_audio(intent)

        print(f"Hook completed successfully", file=sys.stderr)
        sys.stderr.close()
        sys.stderr = original_stderr
        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.close()
        sys.stderr = original_stderr
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
