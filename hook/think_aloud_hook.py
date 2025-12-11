#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Code Think Aloud Hook
============================

Triggers on: PreToolUse, Stop, Notification

Functionality:
1. Extract last thinking content from transcript
2. Skip if no thinking found or same as previous
3. Call translation+TTS API to speak the thinking
4. Error handling with detailed stderr output

Hook behavior: Always allows (never blocks operations)
"""

import sys
import json
import os
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import HTTPError, URLError


# Configuration
API_URL = "http://127.0.0.1:8765/translate_and_speak"
STATE_FILE = Path(__file__).parent / ".last_thinking_hash"


def log_error(message: str):
    """Output error message to stderr."""
    sys.stderr.write(f"[think_aloud_hook ERROR] {message}\n")
    sys.stderr.flush()


def read_stdin_json() -> Dict[str, Any]:
    """Read hook input JSON from stdin."""
    data = sys.stdin.read()
    try:
        return json.loads(data) if data.strip() else {}
    except Exception as e:
        log_error(f"Failed to parse stdin JSON: {e}")
        return {}


def iter_transcript_lines(path: str):
    """Yield each line from transcript JSONL file."""
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield line
    except Exception as e:
        log_error(f"Failed to read transcript: {e}")
        return


def extract_thinking_from_record(record: Dict[str, Any]) -> Optional[str]:
    """
    Extract thinking content from a transcript record.

    Looking for: message.content[].thinking where type == "thinking"
    """
    try:
        # Navigate to message.content
        msg = record.get("message")
        if not isinstance(msg, dict):
            return None

        content = msg.get("content")
        if not isinstance(content, list):
            return None

        # Find thinking blocks
        for item in content:
            if isinstance(item, dict) and item.get("type") == "thinking":
                thinking_text = item.get("thinking")
                if thinking_text and isinstance(thinking_text, str):
                    return thinking_text.strip()

        return None
    except Exception as e:
        log_error(f"Error extracting thinking: {e}")
        return None


def get_last_thinking(transcript_path: Optional[str]) -> Optional[str]:
    """Get the last thinking content from transcript."""
    if not transcript_path:
        return None

    last_thinking = None
    for line in iter_transcript_lines(transcript_path):
        try:
            record = json.loads(line)
        except Exception as e:
            log_error(f"Failed to parse transcript line: {e}")
            continue

        thinking = extract_thinking_from_record(record)
        if thinking:
            last_thinking = thinking

    return last_thinking


def compute_hash(text: str) -> str:
    """Compute MD5 hash of text for comparison."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def read_last_hash() -> Optional[str]:
    """Read the hash of last processed thinking."""
    try:
        if STATE_FILE.exists():
            return STATE_FILE.read_text(encoding="utf-8").strip()
        return None
    except Exception as e:
        log_error(f"Failed to read state file: {e}")
        return None


def write_last_hash(hash_value: str):
    """Write the hash of current thinking."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(hash_value, encoding="utf-8")
    except Exception as e:
        log_error(f"Failed to write state file: {e}")


def call_translation_tts_api(text: str) -> bool:
    """
    Call translation+TTS API with thinking content.

    Returns:
        True if successful, False otherwise
    """
    try:
        payload = {
            "text": text,
            "return_audio": False
        }

        req = request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")

            if status_code == 202:
                return True
            else:
                log_error(f"Unexpected status code: {status_code}")
                log_error(f"Response: {response_body}")
                return False

    except HTTPError as e:
        log_error(f"HTTP error: {e.code}")
        try:
            error_body = e.read().decode("utf-8")
            log_error(f"Response: {error_body}")
        except:
            pass
        return False

    except URLError as e:
        log_error(f"URL error: {e.reason}")
        return False

    except Exception as e:
        log_error(f"API call failed: {e}")
        return False


def main():
    """Main hook logic."""
    # Read hook input
    hook_input = read_stdin_json()
    transcript_path = hook_input.get("transcript_path")

    # Extract last thinking
    thinking = get_last_thinking(transcript_path)

    if not thinking:
        # No thinking found - exit quietly
        sys.exit(0)

    # Check if same as previous
    current_hash = compute_hash(thinking)
    last_hash = read_last_hash()

    if current_hash == last_hash:
        # Same as previous - skip
        sys.exit(0)

    # Call API
    success = call_translation_tts_api(thinking)

    # Always update state to avoid retrying the same content
    write_last_hash(current_hash)

    if success:
        sys.exit(0)
    else:
        # API call failed
        # Error already logged to stderr
        sys.exit(1)


if __name__ == "__main__":
    main()
