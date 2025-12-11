"""
TTS Engine Factory.

Creates VOICEVOX TTS engine based on configuration.
"""

import logging
from pathlib import Path
import yaml

from server.core.tts_voicevox import VoicevoxEngine

logger = logging.getLogger(__name__)


def create_tts_engine(config_path: Path = Path("config.yaml")) -> VoicevoxEngine:
    """
    Create VOICEVOX TTS engine based on configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        VoicevoxEngine instance

    Raises:
        FileNotFoundError: If config file not found
        RuntimeError: If VOICEVOX service unavailable
    """
    # Load configuration
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Get VOICEVOX configuration
    voicevox_config = config.get("voicevox", {})

    logger.info("Creating VOICEVOX TTS engine")

    # Create VOICEVOX engine
    engine = VoicevoxEngine(
        base_url=voicevox_config.get("base_url", "http://localhost:50021"),
        speaker_id=voicevox_config.get("speaker_id", 14),
        timeout=voicevox_config.get("timeout", 30.0)
    )

    logger.info(f"  Base URL: {engine.base_url}")
    logger.info(f"  Speaker ID: {engine.speaker_id}")
    logger.info("VoicevoxEngine created successfully")

    return engine


async def create_tts_engine_with_health_check(
    config_path: Path = Path("config.yaml")
) -> VoicevoxEngine:
    """
    Create VOICEVOX TTS engine and verify service is available.

    Args:
        config_path: Path to configuration file

    Returns:
        VoicevoxEngine instance

    Raises:
        FileNotFoundError: If config file not found
        RuntimeError: If VOICEVOX service unavailable
    """
    engine = create_tts_engine(config_path)

    # Check if VOICEVOX is available
    logger.info("Checking VOICEVOX service health...")
    if not await engine.check_health():
        raise RuntimeError(
            f"VOICEVOX service unavailable at {engine.base_url}. "
            f"Please ensure VOICEVOX is running."
        )

    logger.info("VOICEVOX service is healthy")
    return engine
