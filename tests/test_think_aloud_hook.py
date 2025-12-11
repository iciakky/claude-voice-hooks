#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test script for think_aloud_hook.py"""

import json
import tempfile
from pathlib import Path


def create_test_transcript():
    """Create a test transcript with thinking content."""
    records = [
        # Regular message (no thinking)
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Hello Claude"}]
            }
        },
        # Assistant message with thinking
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "The user is greeting me. I should respond politely and ask how I can help."
                    },
                    {
                        "type": "text",
                        "text": "Hello! How can I help you today?"
                    }
                ]
            }
        },
        # Another assistant message with different thinking
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "This is a test thinking block. It should be the last one extracted."
                    }
                ]
            }
        }
    ]

    # Create temp file
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')
    for record in records:
        tmp.write(json.dumps(record, ensure_ascii=False) + '\n')
    tmp.close()

    return tmp.name


def test_thinking_extraction():
    """Test the thinking extraction logic."""
    # Import the hook module
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "hook"))
    from think_aloud_hook import get_last_thinking, extract_thinking_from_record

    # Create test transcript
    transcript_path = create_test_transcript()
    print(f"Created test transcript: {transcript_path}")

    try:
        # Test extraction
        last_thinking = get_last_thinking(transcript_path)

        print("\n=== Test Results ===")
        if last_thinking:
            print(f"✓ Successfully extracted thinking:")
            print(f"  {last_thinking}")

            expected = "This is a test thinking block. It should be the last one extracted."
            if last_thinking == expected:
                print(f"\n✓ PASS: Extracted correct thinking content")
                return True
            else:
                print(f"\n✗ FAIL: Extracted wrong content")
                print(f"  Expected: {expected}")
                return False
        else:
            print("✗ FAIL: No thinking extracted")
            return False

    finally:
        # Cleanup
        Path(transcript_path).unlink(missing_ok=True)


def test_hash_persistence():
    """Test hash persistence logic."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "hook"))
    from think_aloud_hook import compute_hash, write_last_hash, read_last_hash, STATE_FILE

    print("\n=== Testing Hash Persistence ===")

    # Clean up state file
    STATE_FILE.unlink(missing_ok=True)

    # Test write and read
    test_text = "Test thinking content"
    test_hash = compute_hash(test_text)

    print(f"Hash: {test_hash}")

    write_last_hash(test_hash)
    print(f"✓ Wrote hash to: {STATE_FILE}")

    read_hash = read_last_hash()
    print(f"✓ Read hash: {read_hash}")

    if read_hash == test_hash:
        print("✓ PASS: Hash persistence works correctly")
        return True
    else:
        print("✗ FAIL: Hash mismatch")
        return False


def main():
    print("=" * 60)
    print("Think Aloud Hook Test Suite")
    print("=" * 60)

    test1 = test_thinking_extraction()
    test2 = test_hash_persistence()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
