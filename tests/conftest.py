"""
Pytest configuration and shared fixtures for Phase 1 testing.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir() -> Path:
    """Return the path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_transcript(test_data_dir: Path) -> str:
    """Return sample transcript content."""
    transcript_file = test_data_dir / "sample_transcript.md"
    if transcript_file.exists():
        return transcript_file.read_text(encoding="utf-8")

    # Default sample transcript if file doesn't exist
    return """# Conversation Transcript

## Assistant
I've successfully implemented the user authentication module with JWT tokens.

## User
Great! Now let's test it.

## Assistant
Running tests now...
"""


@pytest.fixture
def sample_hook_request() -> dict:
    """Return a sample hook request payload."""
    return {
        "event": "PostToolUse",
        "tool_name": "Write",
        "transcript_path": "/path/to/transcript.md",
        "timestamp": "2025-12-10T12:00:00Z"
    }


@pytest.fixture
def test_config() -> dict:
    """Return test configuration."""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 8765
        },
        "audio_selector": {
            "type": "classification",
            "audio_dir": "F:\\repo\\claude-voice-hooks\\audio"
        },
        "model_provider": {
            "type": "ollama",
            "ollama": {
                "model": "gemma3n:e4b",
                "base_url": "http://localhost:11434"
            }
        }
    }


@pytest.fixture
def mock_ollama_response() -> dict:
    """Return a mock Ollama classification response."""
    return {
        "model": "gemma3n:e4b",
        "created_at": "2025-12-10T12:00:00Z",
        "response": "completion",
        "done": True
    }


@pytest.fixture
def mock_ollama_client():
    """Return a mock Ollama client."""
    mock = MagicMock()
    mock.generate = AsyncMock(return_value={
        "response": "completion",
        "done": True
    })
    return mock


@pytest.fixture
def audio_files_structure(tmp_path: Path) -> dict:
    """Create a temporary audio directory structure for testing."""
    audio_root = tmp_path / "audio"

    # Create category directories
    categories = ["completion", "failure", "authorization"]
    audio_files = {}

    for category in categories:
        category_dir = audio_root / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy audio files
        audio_files[category] = []
        for i in range(3):
            audio_file = category_dir / f"{category}_{i}.wav"
            audio_file.write_bytes(b"RIFF" + b"\x00" * 100)  # Minimal WAV header
            audio_files[category].append(str(audio_file))

    # Create fallback audio
    fallback = audio_root / "fallback.wav"
    fallback.write_bytes(b"RIFF" + b"\x00" * 100)
    audio_files["fallback"] = str(fallback)

    return {
        "root": str(audio_root),
        "files": audio_files
    }


@pytest.fixture
def mock_transcript_file(tmp_path: Path) -> Path:
    """Create a temporary transcript file."""
    transcript = tmp_path / "transcript.md"
    transcript.write_text("""# Conversation Transcript

## Assistant
Task completed successfully!

## User
Great work!
""", encoding="utf-8")
    return transcript


@pytest.fixture
def env_vars() -> Generator[dict, None, None]:
    """Set up test environment variables and clean up afterwards."""
    original_env = os.environ.copy()

    test_env = {
        "SERVER_HOST": "127.0.0.1",
        "SERVER_PORT": "8765",
        "MODEL_PROVIDER": "ollama",
        "OLLAMA_MODEL": "gemma3n:e4b",
        "AUDIO_MIN_INTERVAL_SEC": "1.5",
        "TEMP_AUDIO_MAX_AGE_HOURS": "24",
        "TEMP_AUDIO_MAX_SIZE_MB": "500"
    }

    os.environ.update(test_env)

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
async def mock_audio_player():
    """Mock audio player that doesn't actually play audio."""
    async def mock_play(audio_file: str):
        """Simulate audio playback."""
        await asyncio.sleep(0.01)  # Simulate very fast playback
        return True

    return mock_play


# Performance testing helpers
@pytest.fixture
def performance_threshold() -> dict:
    """Return performance thresholds for various operations."""
    return {
        "http_response_time_ms": 100,  # Hook should respond in < 100ms
        "model_warmup_time_s": 5,      # Model warmup should take < 5s
        "queue_processing_time_ms": 50, # Queue operations < 50ms
        "end_to_end_time_s": 30        # Complete flow < 30s (includes model inference)
    }


# Utility functions for tests
@pytest.fixture
def create_hook_request():
    """Factory function to create hook requests."""
    def _create(event: str = "PostToolUse",
                tool_name: str = "Write",
                transcript_path: str = None) -> dict:
        return {
            "event": event,
            "tool_name": tool_name,
            "transcript_path": transcript_path or "/tmp/transcript.md",
            "timestamp": "2025-12-10T12:00:00Z"
        }
    return _create
