"""
FastAPI application for Claude Voice Hooks Translation+TTS server.

Provides HTTP endpoints for:
- POST /translate_and_speak: Translate text to Japanese and synthesize speech
- GET /health: Health check with queue statistics

Architecture:
    1. FastAPI receives translation request
    2. Returns 202 immediately (< 100ms)
    3. Background translation worker translates text (Ollama)
    4. Background TTS worker synthesizes and plays audio (VOICEVOX)
    5. No blocking - dual-queue async processing
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from server.config import load_config
from server.core.tts_factory import create_tts_engine_with_health_check
from server.core.translation_tts_worker import TranslationTTSWorkerSystem
from server.models import TranslateAndSpeakRequest, TranslateAndSpeakResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request validation
class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Server status")
    translation_queue_size: int = Field(..., description="Translation queue size")
    tts_queue_size: int = Field(..., description="TTS queue size")
    translation_stats: Dict[str, Any] = Field(..., description="Translation worker statistics")
    tts_stats: Dict[str, Any] = Field(..., description="TTS worker statistics")


# Global state (will be initialized in lifespan)
_config: Optional[Dict[str, Any]] = None
_tts_engine: Optional[Any] = None  # VoicevoxEngine instance
_translation_tts_worker: Optional[TranslationTTSWorkerSystem] = None

# Deduplication state (prevent duplicate requests from concurrent hooks)
_last_translation: Optional[str] = None  # Track last translation text
_last_translation_time: Optional[float] = None  # Track last translation timestamp
_dedup_lock: asyncio.Lock = asyncio.Lock()  # Protect deduplication check


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown:
    - Startup: Load config, initialize VOICEVOX, start Translation+TTS workers
    - Shutdown: Stop workers, cleanup resources
    """
    global _config, _tts_engine, _translation_tts_worker

    # Startup
    logger.info("="*60)
    logger.info("Claude Voice Hooks Server Starting - Translation+TTS")
    logger.info("="*60)

    try:
        # Load configuration
        config_path = None  # Use default config for now
        _config = load_config(config_path)
        logger.info("Configuration loaded successfully")

        # Initialize VOICEVOX TTS Engine and Translation+TTS Worker System
        logger.info("Initializing Translation+TTS system...")
        try:
            # Initialize VOICEVOX TTS engine with health check
            config_path = Path("config.yaml")
            _tts_engine = await create_tts_engine_with_health_check(config_path)
            logger.info(f"  VOICEVOX TTS Engine initialized")
            logger.info(f"  Speaker ID: {_tts_engine.speaker_id}")
            logger.info(f"  Base URL: {_tts_engine.base_url}")

            # Initialize dual-queue worker system
            _translation_tts_worker = TranslationTTSWorkerSystem(_tts_engine)
            await _translation_tts_worker.start()
            logger.info("  Translation+TTS workers started")

        except Exception as e:
            logger.error(f"Failed to initialize Translation+TTS system: {e}", exc_info=True)
            logger.error("Please ensure VOICEVOX is running at http://localhost:50021")
            raise RuntimeError(
                "Translation+TTS system initialization failed. "
                "VOICEVOX service is required."
            )

        # Store in app state for access from endpoints
        app.state.config = _config
        app.state.tts_engine = _tts_engine
        app.state.translation_tts_worker = _translation_tts_worker

        logger.info("="*60)
        logger.info("Server Ready - VOICEVOX Translation+TTS Active")
        logger.info("="*60)

        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    finally:
        # Shutdown
        logger.info("="*60)
        logger.info("Server Shutting Down")
        logger.info("="*60)

        # Stop Translation+TTS workers first
        if _translation_tts_worker:
            logger.info("Stopping Translation+TTS workers...")
            await _translation_tts_worker.stop(timeout=10.0)
            logger.info(f"Translation+TTS workers stopped. Stats: {_translation_tts_worker.stats}")

        # Cleanup VOICEVOX engine resources
        if _tts_engine:
            logger.info("Cleaning up VOICEVOX engine...")
            await _tts_engine.cleanup()
            logger.info("VOICEVOX engine cleanup completed")

        logger.info("="*60)
        logger.info("Server Shutdown Complete")
        logger.info("="*60)


# Create FastAPI application
app = FastAPI(
    title="Claude Voice Hooks Server",
    description="Local server for processing Claude Code hook events with async queue",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns server status and Translation+TTS queue statistics.

    Returns:
        HealthResponse with current server state
    """
    if not _translation_tts_worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server not fully initialized"
        )

    return HealthResponse(
        status="ok",
        translation_queue_size=_translation_tts_worker.get_translation_queue_size(),
        tts_queue_size=_translation_tts_worker.get_tts_queue_size(),
        translation_stats=_translation_tts_worker.stats.get("translation", {}),
        tts_stats=_translation_tts_worker.stats.get("tts", {})
    )


@app.post("/translate_and_speak", response_model=TranslateAndSpeakResponse, status_code=status.HTTP_202_ACCEPTED)
async def translate_and_speak(request: TranslateAndSpeakRequest) -> TranslateAndSpeakResponse:
    """
    Translate English/Chinese text to Japanese and speak it using TTS.

    This endpoint returns immediately (< 100ms) after queueing the request.
    The actual translation and TTS synthesis happen asynchronously in background workers.

    Workflow:
        1. Request queued to translation queue
        2. Background translation worker translates text to Japanese
        3. Japanese text queued to TTS queue
        4. Background TTS worker synthesizes and plays audio

    Args:
        request: TranslateAndSpeakRequest with text and return_audio flag

    Returns:
        TranslateAndSpeakResponse with acceptance confirmation

    Raises:
        HTTPException 503: If Translation+TTS system not initialized
        HTTPException 422: If request validation fails (handled by FastAPI)
    """
    if not _translation_tts_worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation+TTS system not initialized (check server logs for errors)"
        )

    # Deduplication: prevent concurrent hooks from sending duplicate requests
    global _last_translation, _last_translation_time

    try:
        async def dedup_check():
            global _last_translation, _last_translation_time
            async with _dedup_lock:
                current_time = time.time()

                # Check if duplicate: same text AND within 1 second
                is_duplicate = (
                    request.text == _last_translation and
                    _last_translation_time is not None and
                    (current_time - _last_translation_time) <= 1.0
                )

                if not is_duplicate:
                    _last_translation = request.text
                    _last_translation_time = current_time

                return is_duplicate

        # Timeout to prevent deadlock (500ms is generous for simple check)
        is_duplicate = await asyncio.wait_for(dedup_check(), timeout=0.5)

    except asyncio.TimeoutError:
        logger.warning(f"Failed to acquire dedup lock (timeout), rejecting request: {request.text[:50]}...")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server busy (deduplication lock timeout)"
        )

    if is_duplicate:
        logger.info(f"Skipping duplicate request: {request.text[:50]}...")
        return TranslateAndSpeakResponse(
            status="skipped",
            message="Duplicate request ignored",
            queue_position=0
        )

    # Generate unique request ID
    import uuid
    request_id = str(uuid.uuid4())[:8]

    # Log request
    logger.info(f"[{request_id}] /translate_and_speak request: {request.text[:50]}...")

    # Enqueue for translation (background worker will handle rest)
    # Note: Worker will detect『』and skip translation if needed
    await _translation_tts_worker.enqueue_translation(
        text=request.text,
        request_id=request_id,
        return_audio=request.return_audio
    )

    # Get queue position for response
    queue_position = _translation_tts_worker.get_translation_queue_size()

    logger.info(f"[{request_id}] Request queued (position: {queue_position})")

    return TranslateAndSpeakResponse(
        status="queued",
        message=f"Request queued for translation and TTS",
        queue_position=queue_position
    )


@app.get("/")
async def root():
    """Root endpoint - server information."""
    return {
        "message": "Claude Voice Hooks Server - Translation+TTS",
        "version": "0.3.0",
        "endpoints": {
            "health": "/health (GET)",
            "translate_and_speak": "/translate_and_speak (POST)"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """
    Create FastAPI application instance.

    Factory function for testing and custom initialization.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Configured FastAPI application
    """
    # Note: In current implementation, config is loaded in lifespan
    # This function is here for future extensibility and testing
    return app


if __name__ == "__main__":
    # For development: run with uvicorn
    import uvicorn

    logger.info("Starting server in development mode")
    uvicorn.run(
        "server.app:app",
        host="127.0.0.1",
        port=8765,
        reload=True,
        log_level="info"
    )
