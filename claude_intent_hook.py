#!/usr/bin/env python3
"""
Claude Code Intent Classification Hook
Analyzes Claude's last message to classify intent and play corresponding audio feedback.
"""

import asyncio
import json
import sys
import subprocess
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

# Configuration
OLLAMA_MODEL = "gemma3n:e4b"
AUDIO_EXTENSIONS = ('.wav', '.mp3')  # Supported audio formats


@dataclass
class IntentMetadata:
    """Metadata for each intent type."""
    description_zh: str


class Intent(Enum):
    """
    Intent types with embedded configuration.

    This is the single source of truth for all intent definitions.
    Audio files are discovered from filesystem (audio/{intent}/ directory).
    """
    COMPLETION = IntentMetadata(
        description_zh="工作已完成，詢問使用者下一步要做什麼"
    )
    FAILURE = IntentMetadata(
        description_zh="作業失敗或遇到錯誤，請求使用者協助"
    )
    AUTHORIZATION = IntentMetadata(
        description_zh="工作進行中，等待使用者授權或選擇選項"
    )

    @property
    def audio_directory(self) -> Path:
        """Get audio directory for this intent."""
        return Path(__file__).parent / "audio" / str(self)

    @property
    def all_audio_files(self) -> List[Path]:
        """
        Discover all audio files in intent directory.

        Returns:
            List of audio files (.wav, .mp3) in the intent directory
        """
        audio_dir = self.audio_directory

        if not audio_dir.exists():
            return []

        # Get all supported audio files (non-recursive)
        files = []
        for ext in AUDIO_EXTENSIONS:
            files.extend(audio_dir.glob(f"*{ext}"))

        return sorted(files)

    @property
    def audio_file(self) -> str:
        """
        Randomly select audio file, with fallback support.

        Returns:
            Relative path from audio/ directory to play

        Fallback chain:
            1. Random file from intent directory (audio/{intent}/*.wav)
            2. audio/fallback.wav if directory empty/missing
        """
        files = self.all_audio_files

        if files:
            # Random selection from intent directory
            selected = random.choice(files)
            # Return path relative to audio/ directory
            audio_base = Path(__file__).parent / "audio"
            return str(selected.relative_to(audio_base))

        # Fallback to global fallback.wav
        return "fallback.wav"

    @property
    def description_zh(self) -> str:
        """Get Chinese description for this intent."""
        return self.value.description_zh

    def __str__(self) -> str:
        """String representation is lowercase name for consistency."""
        return self.name.lower()


# Derive all configuration from enum (auto-updates when new intents added)
AUDIO_FILES = {str(intent): intent.audio_file for intent in Intent}
VALID_INTENTS = {str(intent) for intent in Intent}
DEFAULT_INTENT = Intent.AUTHORIZATION


def validate_audio_files() -> None:
    """
    Validate audio configuration at startup.

    Checks:
        1. Each intent has at least one audio file OR fallback.wav exists
        2. Warns about empty intent directories (will use fallback)

    Raises:
        FileNotFoundError: If fallback.wav is missing when needed
    """
    audio_base = Path(__file__).parent / "audio"
    fallback_path = audio_base / "fallback.wav"

    warnings = []
    intents_without_audio = []

    for intent in Intent:
        files = intent.all_audio_files

        if not files:
            # Intent directory empty or missing
            intents_without_audio.append(intent)
            warnings.append(
                f"{intent}: No audio files in {intent.audio_directory.name}/ "
                f"(will use fallback.wav)"
            )

    # Check fallback exists if needed
    if intents_without_audio and not fallback_path.exists():
        raise FileNotFoundError(
            f"fallback.wav is required but missing!\n"
            f"The following intents have no audio files:\n" +
            "\n".join(f"  - {intent}" for intent in intents_without_audio) +
            f"\n\nPlease either:\n"
            f"  1. Create audio files in their directories (audio/{{intent}}/)\n"
            f"  2. Create {fallback_path}"
        )

    # Log warnings
    if warnings:
        print("Audio configuration warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)


def build_classification_prompt(message: str) -> str:
    """
    Build classification prompt dynamically from Intent enum.

    Args:
        message: The message to classify

    Returns:
        Formatted prompt for the LLM
    """
    intent_descriptions = "\n".join(
        f"{i+1}. {str(intent)} - {intent.description_zh}"
        for i, intent in enumerate(Intent)
    )

    intent_list = "、".join(str(intent) for intent in Intent)

    return f"""分析以下 AI 助手的訊息，判斷其意圖屬於以下哪一類：

{intent_descriptions}

訊息內容：
{message}

請只回答 {intent_list} 其中之一，不要有其他文字。"""


def extract_key_lines(text: str) -> str:
    """
    Extract first line and last two lines from text for intent classification.

    This optimization reduces token count and focuses on the most informative parts:
    - First line: Usually contains summary or main conclusion
    - Last two lines: Often contain key action items or next steps

    Args:
        text: Full message text

    Returns:
        Extracted key lines joined with newlines
    """
    lines = [line for line in text.split('\n') if line.strip()]

    if not lines:
        return text

    if len(lines) <= 3:
        # If message is short, return as-is
        return text

    # Extract first line + last two lines
    key_lines = [lines[0]] + lines[-2:]
    return '\n'.join(key_lines)


async def read_transcript(transcript_path: str) -> str:
    """
    Read the conversation transcript and extract Claude's last message.

    Returns only the first line and last two lines of the message
    to optimize classification speed and accuracy.
    """
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
                    full_text = ' '.join(text_parts).strip()
                    if full_text:
                        # Extract key lines for classification
                        return extract_key_lines(full_text)
                elif isinstance(content, str) and content.strip():
                    return extract_key_lines(content)

        return ""
    except Exception as e:
        print(f"Error reading transcript: {e}", file=sys.stderr)
        return ""


async def classify_intent(message: str) -> Intent:
    """
    Use local Gemma model to classify Claude's message intent.

    Args:
        message: The message to classify

    Returns:
        Classified Intent enum member, defaults to DEFAULT_INTENT on error
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

        # Validate result and convert to enum
        if result in VALID_INTENTS:
            # Find matching enum member
            for intent in Intent:
                if str(intent) == result:
                    return intent

        # Fallback: try to extract from result
        for intent in Intent:
            if str(intent) in result:
                return intent

        # Default fallback
        print(f"Unable to classify intent from: {result}", file=sys.stderr)
        return DEFAULT_INTENT

    except asyncio.TimeoutError:
        print("Ollama request timed out", file=sys.stderr)
        return DEFAULT_INTENT
    except Exception as e:
        print(f"Error calling Ollama: {e}", file=sys.stderr)
        return DEFAULT_INTENT


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


async def play_intent_audio(intent: Intent) -> bool:
    """
    Play audio feedback for the given intent type.

    Encapsulates audio file resolution, playback orchestration, and stabilization.

    Args:
        intent: The Intent enum member

    Returns:
        True if audio playback was initiated successfully, False otherwise
    """
    audio_file = intent.audio_file  # Returns relative path or "fallback.wav"
    audio_path = Path(__file__).parent / "audio" / audio_file

    print(f"Playing audio for intent '{intent}': {audio_file}", file=sys.stderr)
    await play_audio(str(audio_path))

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
            await play_intent_audio(DEFAULT_INTENT)
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
            await play_intent_audio(DEFAULT_INTENT)
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
