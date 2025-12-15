"""
Triple-queue worker system for Translation + TTS + Audio Playback pipeline.

Architecture:
    TranslationQueue → TranslationWorker → TTSQueue → TTSWorker → AudioPlayQueue → AudioPlayWorker

Workflow:
    1. /translate_and_speak endpoint enqueues request to translation_queue
    2. TranslationWorker dequeues → translates English to Japanese → enqueues to tts_queue
    3. TTSWorker dequeues → generates audio with VOICEVOX → enqueues to audio_play_queue
    4. AudioPlayWorker dequeues → plays audio → deletes temporary file

Benefits:
    - TTS synthesis and audio playback are fully decoupled
    - TTS worker can process next request while previous audio is still playing
    - Maximum parallelism: translation, TTS, and playback all run independently
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from server.core.translation import translate_to_japanese

logger = logging.getLogger(__name__)


@dataclass
class TranslationRequest:
    """Request to translate text."""
    text: str
    request_id: str
    return_audio: bool = False


@dataclass
class TTSRequest:
    """Request to synthesize audio."""
    japanese_text: str
    request_id: str
    return_audio: bool = False


@dataclass
class AudioPlayRequest:
    """Request to play audio file."""
    audio_path: Path
    request_id: str
    delete_after_play: bool = True


class TranslationTTSWorkerSystem:
    """
    Triple-queue worker system for translation, TTS, and audio playback.

    Manages three queues:
    - translation_queue: Stores English/Chinese text waiting for translation
    - tts_queue: Stores Japanese text waiting for TTS synthesis
    - audio_play_queue: Stores audio file paths waiting for playback

    Runs three background workers:
    - translation_worker: Translates and forwards to TTS queue
    - tts_worker: Synthesizes audio and forwards to audio play queue
    - audio_play_worker: Plays audio and deletes temporary files
    """

    def __init__(self, tts_engine: Any):
        """
        Initialize the translation+TTS worker system.

        Args:
            tts_engine: TTS engine instance (VoicevoxEngine)
        """
        self.tts_engine = tts_engine
        self.translation_queue: asyncio.Queue[TranslationRequest] = asyncio.Queue()
        self.tts_queue: asyncio.Queue[TTSRequest] = asyncio.Queue()
        self.audio_play_queue: asyncio.Queue[AudioPlayRequest] = asyncio.Queue()
        self._translation_worker_task: Optional[asyncio.Task] = None
        self._tts_worker_task: Optional[asyncio.Task] = None
        self._audio_play_worker_task: Optional[asyncio.Task] = None
        self._running = False

        # Semaphore to limit TTS concurrency (prevent VRAM overload)
        # Only allow 1 TTS task at a time to avoid GPU memory issues
        self._tts_semaphore = asyncio.Semaphore(1)

        # Statistics
        self.stats = {
            "translation_processed": 0,
            "translation_failed": 0,
            "tts_processed": 0,
            "tts_failed": 0,
            "audio_play_processed": 0,
            "audio_play_failed": 0,
        }

    async def start(self):
        """Start all three background workers."""
        if self._running:
            logger.warning("Workers already running")
            return

        self._running = True
        self._translation_worker_task = asyncio.create_task(self._translation_worker())
        self._tts_worker_task = asyncio.create_task(self._tts_worker())
        self._audio_play_worker_task = asyncio.create_task(self._audio_play_worker())
        logger.info("Translation+TTS+AudioPlay triple-queue workers started")

    async def stop(self, timeout: float = 10.0):
        """Stop all three workers gracefully."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping Translation+TTS+AudioPlay workers...")

        # Cancel worker tasks
        tasks = []
        if self._translation_worker_task:
            self._translation_worker_task.cancel()
            tasks.append(self._translation_worker_task)
        if self._tts_worker_task:
            self._tts_worker_task.cancel()
            tasks.append(self._tts_worker_task)
        if self._audio_play_worker_task:
            self._audio_play_worker_task.cancel()
            tasks.append(self._audio_play_worker_task)

        # Wait for cancellation with timeout
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Worker stop timeout exceeded")

        logger.info(f"Workers stopped. Stats: {self.stats}")

    async def enqueue_translation(self, text: str, request_id: str, return_audio: bool = False):
        """Enqueue a translation request."""
        req = TranslationRequest(text=text, request_id=request_id, return_audio=return_audio)
        await self.translation_queue.put(req)
        logger.info(f"[{request_id}] Enqueued for translation (queue size: {self.translation_queue.qsize()})")

    def get_translation_queue_size(self) -> int:
        """Get current translation queue size."""
        return self.translation_queue.qsize()

    def get_tts_queue_size(self) -> int:
        """Get current TTS queue size."""
        return self.tts_queue.qsize()

    def get_audio_play_queue_size(self) -> int:
        """Get current audio play queue size."""
        return self.audio_play_queue.qsize()

    async def _translation_worker(self):
        """Background worker: translates text and forwards to TTS queue."""
        logger.info("Translation worker started")

        try:
            while self._running:
                try:
                    # Wait for translation request with timeout
                    req = await asyncio.wait_for(
                        self.translation_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                try:
                    logger.info(f"[{req.request_id}] Translating: {req.text[:50]}...")

                    # Check if text is pre-translated Japanese (wrapped in『』)
                    if req.text.startswith("『") and req.text.endswith("』"):
                        # Skip translation, use text as-is (TTS will ignore『』markers)
                        japanese_text = req.text
                        logger.info(f"[{req.request_id}] Pre-translated Japanese detected, skipping model call")
                    else:
                        # Translate to Japanese
                        japanese_text = await translate_to_japanese(req.text)

                    logger.info(f"[{req.request_id}] Translation result: {japanese_text}")

                    # Enqueue to TTS queue
                    tts_req = TTSRequest(
                        japanese_text=japanese_text,
                        request_id=req.request_id,
                        return_audio=req.return_audio
                    )
                    await self.tts_queue.put(tts_req)
                    logger.info(f"[{req.request_id}] Enqueued to TTS queue (size: {self.tts_queue.qsize()})")

                    self.stats["translation_processed"] += 1

                except ValueError as e:
                    # Expected error: Translation validation failed (model crash)
                    logger.warning(f"[{req.request_id}] Translation validation failed: {e}")
                    self.stats["translation_failed"] += 1

                except Exception as e:
                    # Unexpected errors: log with full stack trace
                    logger.error(f"[{req.request_id}] Translation failed: {e}", exc_info=True)
                    self.stats["translation_failed"] += 1

                finally:
                    self.translation_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Translation worker cancelled")
        except Exception as e:
            logger.error(f"Translation worker crashed: {e}", exc_info=True)

    async def _tts_worker(self):
        """Background worker: synthesizes audio and forwards to audio play queue."""
        logger.info("TTS worker started")

        try:
            while self._running:
                try:
                    # Wait for TTS request with timeout
                    req = await asyncio.wait_for(
                        self.tts_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Use semaphore to ensure only one TTS task runs at a time
                # This prevents concurrent requests to VOICEVOX service
                async with self._tts_semaphore:
                    try:
                        logger.info(f"[{req.request_id}] Synthesizing TTS: {req.japanese_text}")
                        logger.info(f"[{req.request_id}] Using request_id for filename: {req.request_id}")

                        # Synthesize audio to temporary file with unique request ID
                        # VOICEVOX engine uses async methods
                        audio_path = await self.tts_engine.synthesize_to_file(
                            req.japanese_text,
                            request_id=req.request_id
                        )
                        logger.info(f"[{req.request_id}] Audio generated: {audio_path.name}")

                        if not req.return_audio:
                            # Enqueue to audio play queue
                            play_req = AudioPlayRequest(
                                audio_path=audio_path,
                                request_id=req.request_id,
                                delete_after_play=True
                            )
                            await self.audio_play_queue.put(play_req)
                            logger.info(f"[{req.request_id}] Enqueued to audio play queue (size: {self.audio_play_queue.qsize()})")
                        else:
                            # For return_audio mode, just log (caller would need to handle response)
                            logger.info(f"[{req.request_id}] Audio ready at {audio_path} (return_audio=True)")

                        self.stats["tts_processed"] += 1

                        # Short delay after synthesis to allow GPU cache cleanup
                        await asyncio.sleep(0.1)

                    except asyncio.TimeoutError:
                        # Expected error: VOICEVOX processing timeout
                        # Log concisely without full stack trace
                        timeout_val = getattr(self.tts_engine, 'timeout_seconds', 'unknown')
                        text_preview = req.japanese_text[:100] + ('...' if len(req.japanese_text) > 100 else '')
                        logger.warning(
                            f"[{req.request_id}] TTS timeout after {timeout_val}s. "
                            f"VOICEVOX took too long to process text: {text_preview}"
                        )
                        self.stats["tts_failed"] += 1

                    except Exception as e:
                        # Unexpected errors: log with full stack trace for debugging
                        logger.error(f"[{req.request_id}] TTS failed: {e}", exc_info=True)
                        self.stats["tts_failed"] += 1

                    finally:
                        self.tts_queue.task_done()

        except asyncio.CancelledError:
            logger.info("TTS worker cancelled")
        except Exception as e:
            logger.error(f"TTS worker crashed: {e}", exc_info=True)

    async def _audio_play_worker(self):
        """Background worker: plays audio and deletes temporary files."""
        logger.info("Audio play worker started")

        try:
            while self._running:
                try:
                    # Wait for audio play request with timeout
                    req = await asyncio.wait_for(
                        self.audio_play_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                try:
                    logger.info(f"[{req.request_id}] Playing audio: {req.audio_path.name}")
                    logger.info(f"[{req.request_id}] Audio file exists: {req.audio_path.exists()}")
                    logger.info(f"[{req.request_id}] Audio file size: {req.audio_path.stat().st_size if req.audio_path.exists() else 'N/A'} bytes")

                    # Play audio
                    await self._play_audio(req.audio_path)
                    logger.info(f"[{req.request_id}] Audio played successfully")

                    # Delete temporary file if requested
                    if req.delete_after_play:
                        try:
                            if req.audio_path.exists():
                                req.audio_path.unlink()
                                logger.info(f"[{req.request_id}] Deleted temporary file: {req.audio_path.name}")
                            else:
                                logger.warning(f"[{req.request_id}] File already deleted: {req.audio_path.name}")
                        except Exception as e:
                            logger.warning(f"[{req.request_id}] Failed to delete temporary file: {e}")

                    self.stats["audio_play_processed"] += 1

                except Exception as e:
                    logger.error(f"[{req.request_id}] Audio playback failed: {e}", exc_info=True)
                    logger.error(f"[{req.request_id}] Failed audio path: {req.audio_path}")
                    self.stats["audio_play_failed"] += 1

                finally:
                    self.audio_play_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Audio play worker cancelled")
        except Exception as e:
            logger.error(f"Audio play worker crashed: {e}", exc_info=True)

    async def _play_audio(self, audio_path: Path):
        """
        Play audio file using system audio player.

        Args:
            audio_path: Path to WAV audio file
        """
        # Choose player based on platform
        if sys.platform == "win32":
            cmd = ['powershell', '-Command', f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()']
        elif sys.platform == "darwin":
            cmd = ['afplay', str(audio_path)]
        else:
            cmd = ['aplay', str(audio_path)]

        # Execute and wait for completion
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        await process.wait()
        logger.debug(f"Audio playback completed: {audio_path.name}")


# Global instance (will be initialized in server startup)
_worker_system: Optional[TranslationTTSWorkerSystem] = None


def get_worker_system() -> Optional[TranslationTTSWorkerSystem]:
    """Get the global worker system instance."""
    return _worker_system


def set_worker_system(system: TranslationTTSWorkerSystem):
    """Set the global worker system instance."""
    global _worker_system
    _worker_system = system
