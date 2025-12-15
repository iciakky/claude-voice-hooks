"""
Translation logging utility for quality analysis.

Records all Ollama translation calls in JSONL format for later LLM analysis.
Designed to be non-intrusive - logging failures never disrupt translation pipeline.
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cache git hash at module initialization (avoid repeated subprocess calls)
_cached_git_hash: Optional[str] = None


def _get_git_hash() -> str:
    """Get current git commit hash (cached at first call)."""
    global _cached_git_hash
    if _cached_git_hash is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).parent.parent.parent,  # repo root
                capture_output=True,
                text=True,
                timeout=2.0
            )
            if result.returncode == 0:
                _cached_git_hash = result.stdout.strip()
            else:
                _cached_git_hash = "unknown"
        except Exception as e:
            logger.debug(f"Failed to get git hash: {e}")
            _cached_git_hash = "unknown"
    return _cached_git_hash


def _get_modelfile_name() -> str:
    """Get Ollama model name from environment variable."""
    return os.environ.get("OLLAMA_MODEL", "my-translator")


def _get_log_file_path() -> Path:
    """Get today's log file path: logs/translation_YYYY-MM-DD.jsonl"""
    today = datetime.now().strftime("%Y-%m-%d")
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir / f"translation_{today}.jsonl"


def _append_to_file(file_path: Path, content: str) -> None:
    """Synchronous file append operation (called from executor)."""
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)


async def log_translation(source_text: str, translated_text: str) -> None:
    """
    Log translation to JSONL file for quality analysis.

    Records:
    - source_text: Original input text
    - translated_text: Raw translation BEFORE post-processing
    - timestamp: ISO 8601 format, second precision
    - modelfile: Ollama model name (from OLLAMA_MODEL env var)
    - git_hash: Current git commit hash

    Args:
        source_text: Original text before translation
        translated_text: Raw translated text (BEFORE postprocess_for_tts)

    Note:
        This function never raises exceptions - all errors are logged and swallowed
        to prevent disrupting the translation pipeline.
    """
    try:
        # Prepare log entry
        entry = {
            "source_text": source_text,
            "translated_text": translated_text,
            "timestamp": datetime.now().isoformat(timespec='seconds'),  # 2025-12-15T14:30:45
            "modelfile": _get_modelfile_name(),
            "git_hash": _get_git_hash()
        }

        # Write to log file (async I/O)
        log_file = _get_log_file_path()
        json_line = json.dumps(entry, ensure_ascii=False) + "\n"

        # Use asyncio file I/O to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _append_to_file,
            log_file,
            json_line
        )

        logger.debug(f"Translation logged to {log_file}")

    except Exception as e:
        # CRITICAL: Never let logging failures break translation
        logger.warning(f"Failed to log translation: {e}")
