#!/usr/bin/env python3
"""
Claude Code Intent Classification Hook
Analyzes Claude's last message to classify intent and play corresponding audio feedback.
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Literal

# Configuration
OLLAMA_MODEL = "gemma3n:e4b"
AUDIO_FILES = {
    "completion": "completion.wav",  # 工作完成詢問下一步
    "failure": "failure.wav",        # 作業失敗請求協助
    "authorization": "authorization.wav"  # 等待使用者授權或選擇
}

IntentType = Literal["completion", "failure", "authorization"]


async def read_transcript(transcript_path: str) -> str:
    """Read the conversation transcript and extract Claude's last message."""
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse JSONL format - each line is a JSON object
        messages = [json.loads(line) for line in lines if line.strip()]

        # Find the last assistant message
        for msg in reversed(messages):
            if msg.get('role') == 'assistant':
                # Extract text content from the message
                content = msg.get('content', [])
                if isinstance(content, list):
                    text_parts = [
                        block.get('text', '')
                        for block in content
                        if block.get('type') == 'text'
                    ]
                    return ' '.join(text_parts)
                elif isinstance(content, str):
                    return content

        return ""
    except Exception as e:
        print(f"Error reading transcript: {e}", file=sys.stderr)
        return ""


async def classify_intent(message: str) -> IntentType:
    """Use local Gemma model to classify Claude's message intent."""

    prompt = f"""分析以下 AI 助手的訊息，判斷其意圖屬於以下哪一類：

1. completion - 工作已完成，詢問使用者下一步要做什麼
2. failure - 工作失敗或遇到錯誤，請求使用者協助
3. authorization - 工作進行中，等待使用者授權或選擇選項

訊息內容：
{message}

請只回答 completion、failure 或 authorization 其中之一，不要有其他文字。"""

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

        # Validate result
        if result in ['completion', 'failure', 'authorization']:
            return result

        # Fallback: try to extract from result
        for intent in ['completion', 'failure', 'authorization']:
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

    # 🔍 診斷點 1: 檔案是否存在
    print(f"[DEBUG] Checking audio file: {audio_path}", file=sys.stderr)
    print(f"[DEBUG] File exists: {audio_path.exists()}", file=sys.stderr)
    print(f"[DEBUG] Absolute path: {audio_path.absolute()}", file=sys.stderr)

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

        # 🔍 診斷點 2: 命令內容
        print(f"[DEBUG] Running command: {' '.join(cmd)}", file=sys.stderr)

        # Run in background without waiting
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 🔍 診斷點 3: 程序狀態
        print(f"[DEBUG] Process started, PID: {process.pid}", file=sys.stderr)

        # ⭐ 修復 Race Condition：等待程序啟動
        await asyncio.sleep(0.1)  # 給程序 100ms 啟動時間
        poll_result = process.poll()
        print(f"[DEBUG] Process poll result: {poll_result} (None=running)", file=sys.stderr)

        if poll_result is not None:
            print(f"[ERROR] Process exited immediately with code: {poll_result}", file=sys.stderr)

    except Exception as e:
        print(f"Error playing audio: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


async def main():
    """Main hook execution."""
    # 🔍 診斷：記錄 Hook 已觸發 + 重定向 stderr 到檔案
    from datetime import datetime
    trigger_log = Path(__file__).parent / "hook_triggered.log"
    debug_log = Path(__file__).parent / "hook_debug.log"

    with open(trigger_log, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Hook triggered\n")

    # 重定向 stderr 到檔案
    original_stderr = sys.stderr
    sys.stderr = open(debug_log, 'a', encoding='utf-8')
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Hook started at {datetime.now().isoformat()}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    try:
        # Read hook input from stdin
        hook_input = json.loads(sys.stdin.read())

        # 🔍 診斷：顯示完整 hook 輸入
        print(f"Hook input: {json.dumps(hook_input, indent=2)}", file=sys.stderr)

        hook_event = hook_input.get('hook_event_name')
        print(f"Hook event: {hook_event}", file=sys.stderr)

        # ⭐ 優先處理：Notification hook 直接播放預設音效
        if hook_event == 'Notification':
            print("Notification hook detected - playing default authorization sound", file=sys.stderr)
            await play_audio(AUDIO_FILES['authorization'])
            await asyncio.sleep(1.5)
            # Notification hook: 空輸出或不輸出 JSON
            print(f"Hook completed (Notification mode)", file=sys.stderr)
            sys.stderr.close()
            sys.stderr = original_stderr
            sys.exit(0)

        # Stop hook 流程：需要分類 intent
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
            print("Playing default authorization sound", file=sys.stderr)
            await play_audio(AUDIO_FILES['authorization'])
            await asyncio.sleep(1.5)
            sys.stderr.close()
            sys.stderr = original_stderr
            sys.exit(0)

        # Classify intent
        intent = await classify_intent(last_message)
        print(f"Classified intent: {intent}", file=sys.stderr)

        # Play corresponding audio (non-blocking)
        audio_file = AUDIO_FILES.get(intent)
        if audio_file:
            await play_audio(audio_file)

            # ⭐ 修復 Race Condition：確保音效程序啟動
            await asyncio.sleep(1.0)  # 給音效播放器 1 秒啟動時間
            print("[DEBUG] Waited for audio process to stabilize", file=sys.stderr)

        # Stop hook: 不需要返回控制 JSON，只輸出 metadata 到 stderr
        print(f"[RESULT] Intent: {intent}, Audio: {audio_file}", file=sys.stderr)
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
