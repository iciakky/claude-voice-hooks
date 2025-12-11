#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""End-to-end test for think_aloud_hook.py"""

import json
import subprocess
import tempfile
from pathlib import Path


def create_test_transcript_with_real_structure():
    """Create a test transcript matching the real Claude Code format."""
    record = {
        "parentUuid": "f4e8fc81-c6a2-40d6-aeba-683cf2e78616",
        "isSidechain": False,
        "userType": "external",
        "cwd": "F:\\repo\\test",
        "sessionId": "e84137db-74c3-4157-a849-f41111945cc2",
        "version": "2.0.28",
        "gitBranch": "",
        "type": "assistant",
        "timestamp": "2025-10-28T19:58:39.165Z",
        "message": {
            "model": "claude-sonnet-4-5-20250929",
            "id": "msg_test123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "thinking",
                    "thinking": "Testing the hook with a sample thinking. This should be translated to Japanese and spoken."
                }
            ],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {
                "input_tokens": 8,
                "output_tokens": 4
            }
        },
        "uuid": "8202c454-e703-47f8-b7a9-c5f27445b793"
    }

    # Create temp file
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')
    tmp.write(json.dumps(record, ensure_ascii=False) + '\n')
    tmp.close()

    return tmp.name


def test_hook_execution_no_api():
    """Test hook execution without calling actual API (server may not be running)."""
    print("=" * 60)
    print("E2E Test: Hook Execution (No API Call)")
    print("=" * 60)

    # Create test transcript
    transcript_path = create_test_transcript_with_real_structure()
    print(f"\n✓ Created test transcript: {transcript_path}")

    # Prepare hook input
    hook_input = {
        "transcript_path": transcript_path,
        "hook_event_name": "Stop"
    }
    hook_input_json = json.dumps(hook_input)

    print(f"✓ Hook input prepared")

    # Call hook script
    hook_script = Path(__file__).parent / "hook" / "think_aloud_hook.py"
    print(f"✓ Hook script: {hook_script}")

    try:
        # Note: This will fail at API call stage if server is not running
        # But we can verify the extraction logic works
        result = subprocess.run(
            ["python", str(hook_script)],
            input=hook_input_json,
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"\n--- Execution Result ---")
        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print(f"Stdout:\n{result.stdout}")

        if result.stderr:
            print(f"Stderr:\n{result.stderr}")

        # Check if stderr contains expected error (API not reachable)
        if "API call failed" in result.stderr or "URL error" in result.stderr:
            print("\n✓ PASS: Hook executed and attempted API call")
            print("  (API call failed as expected if server not running)")
            return True
        elif result.returncode == 0:
            print("\n✓ PASS: Hook executed successfully")
            print("  (API server must be running)")
            return True
        else:
            print("\n⚠ Hook executed but returned non-zero exit code")
            return False

    except subprocess.TimeoutExpired:
        print("\n✗ FAIL: Hook execution timeout")
        return False
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        return False
    finally:
        Path(transcript_path).unlink(missing_ok=True)


def test_duplicate_detection():
    """Test that duplicate thinking is skipped."""
    print("\n" + "=" * 60)
    print("E2E Test: Duplicate Detection")
    print("=" * 60)

    # Create test transcript
    transcript_path = create_test_transcript_with_real_structure()
    print(f"\n✓ Created test transcript")

    hook_input = {
        "transcript_path": transcript_path,
        "hook_event_name": "Stop"
    }
    hook_input_json = json.dumps(hook_input)

    hook_script = Path(__file__).parent / "hook" / "think_aloud_hook.py"

    # First run - should process
    print("\n--- First run (should process) ---")
    result1 = subprocess.run(
        ["python", str(hook_script)],
        input=hook_input_json,
        capture_output=True,
        text=True,
        timeout=10
    )
    print(f"Exit code: {result1.returncode}")
    if result1.stderr:
        print(f"Stderr: {result1.stderr[:200]}")

    # Second run - should skip (duplicate)
    print("\n--- Second run (should skip duplicate) ---")
    result2 = subprocess.run(
        ["python", str(hook_script)],
        input=hook_input_json,
        capture_output=True,
        text=True,
        timeout=10
    )
    print(f"Exit code: {result2.returncode}")
    print(f"Stderr length: {len(result2.stderr)}")

    if result2.returncode == 0 and len(result2.stderr) == 0:
        print("\n✓ PASS: Duplicate was skipped (no errors)")
        return True
    else:
        print("\n⚠ Result differs from expected")
        return False


def main():
    print("=" * 60)
    print("Think Aloud Hook - End-to-End Tests")
    print("=" * 60)

    test1 = test_hook_execution_no_api()
    test2 = test_duplicate_detection()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Test 1 (Hook Execution): {'PASS' if test1 else 'FAIL'}")
    print(f"Test 2 (Duplicate Detection): {'PASS' if test2 else 'FAIL'}")

    if test1 and test2:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
