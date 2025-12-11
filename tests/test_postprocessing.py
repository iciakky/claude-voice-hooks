"""Test the TTS post-processing transformations."""
from server.core.translation import postprocess_for_tts

# Test cases
test_cases = [
    # (input, expected_output, description)
    # Explanation removal tests
    ("認証機能を実装しました Explanation: This means authentication", "認証機能を実装しました", "Remove Explanation (capitalized)"),
    ("設定を追加 explanation: added settings", "設定を追加", "Remove explanation (lowercase)"),
    ("ファイルを更新\nEXPLANATION: Updated files", "ファイルを更新", "Remove EXPLANATION (uppercase)"),
    ("翻訳完了 Explanation:\nThis is a long explanation\nwith multiple lines", "翻訳完了", "Remove multiline explanation"),
    
    # Fraction tests
    ("1/2の確率", "1分の2の確率", "Simple fraction"),
    ("3/4カップ", "3分の4カップ", "Fraction in cooking"),
    ("成功率は5/10でした", "成功率は5分の10でした", "Fraction in sentence"),
    
    # Decimal tests
    ("バージョン3.2をリリースしました", "バージョン3てん2をリリースしました", "Decimal point"),
    ("Python 3.11.5が必要です", "Python 3てん11てん5が必要です", "Multiple decimal points"),
    
    # Symbol tests
    ("my-translatorを使用", "my translatorを使用", "Hyphen in my-translator"),
    ("test_file.pyを修正", "test file pyを修正", "Underscore and period"),
    ("config.yamlを追加", "config yamlを追加", "Period in filename"),
    ("v1.2.3のアップデート", "v1てん2てん3のアップデート", "Version numbers"),
    ("API-endpointとDB_connectionを統合", "API endpointとDB connectionを統合", "Hyphens and underscores"),
    
    # Combined tests
    ("1/2は0.5に等しい", "1分の2は0てん5に等しい", "Fraction and decimal"),
    ("設定追加、統合、修正", "設定追加、統合、修正", "No changes needed (Japanese only)"),
]

print("=" * 80)
print("TTS Post-Processing Test")
print("=" * 80)

passed = 0
failed = 0

for input_text, expected, description in test_cases:
    result = postprocess_for_tts(input_text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status} - {description}")
    print(f"  Input:    \"{input_text[:60]}...\"" if len(input_text) > 60 else f"  Input:    \"{input_text}\"")
    print(f"  Expected: \"{expected}\"")
    print(f"  Got:      \"{result}\"")
    
    if result != expected:
        print(f"  ⚠️  Mismatch!")

print("\n" + "=" * 80)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 80)

if failed == 0:
    print("\n🎉 All tests passed! Ready for deployment.")
else:
    print(f"\n⚠️  {failed} test(s) failed. Review implementation.")
