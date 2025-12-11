#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test triple-queue concurrency and parallelism."""

import asyncio
import time
import httpx


async def send_request(client: httpx.AsyncClient, text: str, request_num: int):
    """Send a single translation+TTS request."""
    start_time = time.time()

    payload = {
        "text": text,
        "return_audio": False
    }

    try:
        response = await client.post(
            "http://127.0.0.1:8765/translate_and_speak",
            json=payload,
            timeout=5.0
        )
        response_time = time.time() - start_time

        return {
            "request_num": request_num,
            "status": response.status_code,
            "response_time": response_time,
            "success": response.status_code == 202
        }
    except Exception as e:
        return {
            "request_num": request_num,
            "status": "error",
            "response_time": time.time() - start_time,
            "success": False,
            "error": str(e)
        }


async def test_concurrency():
    """Test concurrent requests to verify non-blocking behavior."""
    print("=" * 70)
    print("Triple-Queue Concurrency Test")
    print("=" * 70)
    print("\nObjective: Verify TTS synthesis doesn't block during audio playback")
    print("Expected: All API responses should return in < 1s regardless of TTS/playback time\n")

    # Prepare test requests
    test_texts = [
        "Request number one. This is a test of the triple queue architecture.",
        "Request number two. Testing concurrent translation and TTS processing.",
        "Request number three. Verifying audio playback doesn't block TTS synthesis.",
        "Request number four. The system should handle multiple requests in parallel.",
        "Request number five. Final test request to validate full pipeline.",
    ]

    print(f"Sending {len(test_texts)} concurrent requests...\n")

    start_time = time.time()

    async with httpx.AsyncClient() as client:
        # Send all requests concurrently
        tasks = [
            send_request(client, text, i + 1)
            for i, text in enumerate(test_texts)
        ]
        results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # Analyze results
    print("Results:")
    print("-" * 70)

    success_count = 0
    for result in results:
        status_symbol = "✓" if result["success"] else "✗"
        print(f"{status_symbol} Request {result['request_num']}: "
              f"Status={result['status']}, "
              f"Response time={result['response_time']:.3f}s")
        if result["success"]:
            success_count += 1
        elif "error" in result:
            print(f"  Error: {result['error']}")

    print("-" * 70)
    print(f"\nSummary:")
    print(f"  Total requests: {len(results)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {len(results) - success_count}")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average response time: {sum(r['response_time'] for r in results) / len(results):.3f}s")

    # Check health endpoint
    print("\n" + "=" * 70)
    print("Checking server health and queue statistics...")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://127.0.0.1:8765/health", timeout=5.0)
            if response.status_code == 200:
                health_data = response.json()
                print("\nServer Health:")
                print(f"  Status: {health_data.get('status')}")
                print(f"  Model warmed up: {health_data.get('model_warmed_up')}")

                # Wait a bit to see queue processing
                print("\nWaiting 5 seconds to observe queue processing...")
                await asyncio.sleep(5)

                response = await client.get("http://127.0.0.1:8765/health", timeout=5.0)
                health_data = response.json()

                print("\nQueue Statistics (after 5 seconds):")
                print(f"  Translation queue: {health_data.get('queue_size', 'N/A')}")
                # Note: May need to update health endpoint to show all 3 queues

        except Exception as e:
            print(f"\nError checking health: {e}")

    # Verdict
    print("\n" + "=" * 70)
    if success_count == len(results):
        max_response_time = max(r['response_time'] for r in results)
        if max_response_time < 1.0:
            print("✓ PASS: All requests succeeded with fast response times")
            print(f"  Maximum response time: {max_response_time:.3f}s")
            print("  Triple-queue architecture is working correctly!")
        else:
            print("⚠ PARTIAL: All requests succeeded but some were slow")
            print(f"  Maximum response time: {max_response_time:.3f}s")
            print("  May need further optimization")
    else:
        print("✗ FAIL: Some requests failed")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_concurrency())
