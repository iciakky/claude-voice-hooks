"""
VOICEVOX TTS Engine Implementation.

Provides text-to-speech synthesis using VOICEVOX Engine API.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class VoicevoxEngine:
    """
    VOICEVOX TTS engine client.

    Workflow:
        1. POST /audio_query?text={text}&speaker={speaker_id}
           → Returns AudioQuery JSON object
        2. POST /synthesis?speaker={speaker_id} with AudioQuery as body
           → Returns binary WAV audio

    Args:
        base_url: VOICEVOX Engine API base URL (default: http://localhost:50021)
        speaker_id: Default speaker ID (default: 20)
        timeout: HTTP request timeout in seconds (default: 30.0)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:50021",
        speaker_id: int = 20,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.speaker_id = speaker_id
        self.timeout_seconds = timeout  # Store for error messages
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(f"VoicevoxEngine initialized: {self.base_url}")
        logger.info(f"  Default speaker ID: {self.speaker_id}")
        logger.info(f"  Timeout: {self.timeout_seconds}s")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def check_health(self) -> bool:
        """
        Check if VOICEVOX Engine is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/version") as resp:
                if resp.status == 200:
                    version = await resp.text()
                    logger.info(f"VOICEVOX Engine version: {version}")
                    return True
                return False
        except Exception as e:
            logger.error(f"VOICEVOX health check failed: {e}")
            return False

    async def get_speakers(self) -> list[Dict[str, Any]]:
        """
        Get list of available speakers.

        Returns:
            List of speaker objects with name, uuid, styles

        Example:
            [
                {
                    "name": "ずんだもん",
                    "speaker_uuid": "...",
                    "styles": [
                        {"name": "ノーマル", "id": 3, "type": "talk"}
                    ]
                }
            ]
        """
        session = await self._get_session()
        async with session.get(f"{self.base_url}/speakers") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def synthesize(
        self,
        text: str,
        speaker_id: Optional[int] = None,
        speed_scale: float = 1.0,
        pitch_scale: float = 1.0,
        volume_scale: float = 1.0
    ) -> bytes:
        """
        Synthesize speech from Japanese text.

        Args:
            text: Japanese text to synthesize
            speaker_id: Speaker ID (default: use instance default)
            speed_scale: Speed multiplier (0.5-2.0, default: 1.0)
            pitch_scale: Pitch multiplier (0.5-2.0, default: 1.0)
            volume_scale: Volume multiplier (0.5-2.0, default: 1.0)

        Returns:
            WAV audio bytes

        Raises:
            aiohttp.ClientError: If API request fails
            ValueError: If text is empty
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("text is required")

        speaker = speaker_id if speaker_id is not None else self.speaker_id
        session = await self._get_session()

        # Step 1: Generate AudioQuery
        logger.debug(f"Generating AudioQuery for: {text[:50]}...")
        async with session.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": speaker}
        ) as resp:
            resp.raise_for_status()
            audio_query = await resp.json()

        # Modify AudioQuery parameters if non-default
        if speed_scale != 1.0:
            audio_query["speedScale"] = speed_scale
        if pitch_scale != 1.0:
            audio_query["pitchScale"] = pitch_scale
        if volume_scale != 1.0:
            audio_query["volumeScale"] = volume_scale

        # Step 2: Synthesize audio
        logger.debug(f"Synthesizing audio with speaker {speaker}")
        async with session.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker},
            json=audio_query
        ) as resp:
            resp.raise_for_status()
            wav_bytes = await resp.read()

        logger.info(f"Synthesized {len(wav_bytes)} bytes of audio")
        return wav_bytes

    async def synthesize_to_file(
        self,
        text: str,
        prompt_text: Optional[str] = None,  # Ignored (legacy compatibility)
        top_k: Optional[int] = None,  # Ignored (legacy compatibility)
        top_p: Optional[float] = None,  # Ignored (legacy compatibility)
        temperature: Optional[float] = None,  # Ignored (legacy compatibility)
        speed: Optional[float] = None,  # Mapped to speed_scale
        request_id: Optional[str] = None,
        speaker_id: Optional[int] = None,
        **kwargs
    ) -> Path:
        """
        Synthesize speech and save to temporary WAV file.

        Args:
            text: Japanese text to synthesize
            prompt_text: Ignored (legacy compatibility)
            top_k: Ignored (legacy compatibility)
            top_p: Ignored (legacy compatibility)
            temperature: Ignored (legacy compatibility)
            speed: Speed multiplier (0.5-2.0), mapped to speed_scale
            request_id: Optional request ID for filename
            speaker_id: Speaker ID (default: use instance default)
            **kwargs: Additional parameters (pitch_scale, volume_scale)

        Returns:
            Path to generated WAV file in audio/tmp/

        Raises:
            aiohttp.ClientError: If API request fails
            ValueError: If text is empty
        """
        # Map speed parameter to VOICEVOX speed_scale
        speed_scale = speed if speed is not None else kwargs.get('speed_scale', 1.0)

        # Generate audio
        synthesize_kwargs = {
            'speaker_id': speaker_id,
            'speed_scale': speed_scale,
            'pitch_scale': kwargs.get('pitch_scale', 1.0),
            'volume_scale': kwargs.get('volume_scale', 1.0)
        }
        wav_bytes = await self.synthesize(text, **synthesize_kwargs)

        # Save to temporary file
        output_dir = Path("audio/tmp")
        output_dir.mkdir(parents=True, exist_ok=True)

        if request_id:
            output_path = output_dir / f"tts_{request_id}.wav"
        else:
            import uuid
            output_path = output_dir / f"tts_{uuid.uuid4().hex[:8]}.wav"

        output_path.write_bytes(wav_bytes)
        logger.info(f"Saved audio to {output_path}")

        return output_path

    async def cleanup(self):
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("VoicevoxEngine session closed")

    def __del__(self):
        """Cleanup on deletion (fallback)."""
        if self._session and not self._session.closed:
            # Note: In async context, should use cleanup() explicitly
            try:
                asyncio.get_event_loop().run_until_complete(self.cleanup())
            except Exception:
                pass
