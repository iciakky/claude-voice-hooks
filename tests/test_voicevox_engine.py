"""
Test script for VOICEVOX TTS engine.

Tests basic functionality:
1. Health check
2. Speaker list retrieval
3. Text synthesis
4. File synthesis
"""

import asyncio
import logging
from pathlib import Path

from server.core.tts_voicevox import VoicevoxEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_voicevox():
    """Test VOICEVOX engine functionality."""
    logger.info("="*60)
    logger.info("VOICEVOX Engine Test")
    logger.info("="*60)

    # Initialize engine
    engine = VoicevoxEngine(
        base_url="http://localhost:50021",
        speaker_id=14,
        timeout=30.0
    )

    try:
        # Test 1: Health check
        logger.info("\n[Test 1] Health Check")
        is_healthy = await engine.check_health()
        if is_healthy:
            logger.info("✓ VOICEVOX service is healthy")
        else:
            logger.error("✗ VOICEVOX service is unavailable")
            return

        # Test 2: Get speakers
        logger.info("\n[Test 2] Get Available Speakers")
        speakers = await engine.get_speakers()
        logger.info(f"Found {len(speakers)} speakers:")
        for speaker in speakers[:3]:  # Show first 3
            logger.info(f"  - {speaker['name']}: {len(speaker['styles'])} styles")
            for style in speaker['styles'][:2]:  # Show first 2 styles
                logger.info(f"    - {style['name']} (ID: {style['id']})")

        # Test 3: Synthesize to bytes
        logger.info("\n[Test 3] Synthesize Japanese Text to Bytes")
        test_text = "サーバーの準備ができました。テストを開始してください。"
        logger.info(f"Text: {test_text}")

        wav_bytes = await engine.synthesize(test_text)
        logger.info(f"✓ Synthesized {len(wav_bytes)} bytes of audio")

        # Test 4: Synthesize to file
        logger.info("\n[Test 4] Synthesize to File")
        output_path = await engine.synthesize_to_file(
            text=test_text,
            request_id="test_001"
        )
        logger.info(f"✓ Audio saved to: {output_path}")
        logger.info(f"  File size: {output_path.stat().st_size} bytes")
        logger.info(f"  File exists: {output_path.exists()}")

        # Test 5: Test with modified parameters
        logger.info("\n[Test 5] Synthesize with Modified Parameters")
        test_text_2 = "処理が完了しました。"
        logger.info(f"Text: {test_text_2}")

        wav_bytes_2 = await engine.synthesize(
            text=test_text_2,
            speed_scale=1.2,  # Faster
            pitch_scale=1.1,  # Higher pitch
            volume_scale=1.0
        )
        logger.info(f"✓ Synthesized {len(wav_bytes_2)} bytes with custom parameters")

        # Test 6: Multiple requests (concurrency test)
        logger.info("\n[Test 6] Concurrent Synthesis Test")
        test_texts = [
            "タスク完了しました",
            "エラーが発生しました",
            "承認待ちです"
        ]

        tasks = [
            engine.synthesize_to_file(text=text, request_id=f"concurrent_{i}")
            for i, text in enumerate(test_texts)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if isinstance(r, Path))
        logger.info(f"✓ Concurrent synthesis: {success_count}/{len(test_texts)} successful")

        for i, result in enumerate(results):
            if isinstance(result, Path):
                logger.info(f"  - Request {i}: {result.name} ({result.stat().st_size} bytes)")
            else:
                logger.error(f"  - Request {i}: Failed - {result}")

        logger.info("\n" + "="*60)
        logger.info("All tests completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

    finally:
        # Cleanup
        await engine.cleanup()
        logger.info("Engine cleanup completed")


if __name__ == "__main__":
    asyncio.run(test_voicevox())
