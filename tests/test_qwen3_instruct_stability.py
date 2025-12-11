"""Stability test for qwen3:4b-instruct (no thinking, fast).

User confirmed:
- qwen3:4b-instruct doesn't output thinking process
- Faster than phi3:mini
- No need for /no_think suffix

Testing: 5 scenarios × 5 runs = 25 translations
"""
import asyncio
import time
import statistics
import re
import ollama

PLAN_B_V2 = """You produce CONCISE spoken Japanese summaries for text-to-speech.

GOOD example (concise natural narrative):
"認証機能まわりの実装を一通り整えました。JWTトークンへの移行、パスワードハッシュの強化、レート制限の追加が完了しています。"

BAD example (forbidden enumeration with symbols):
"以下のファイルを修正：1. login.py 2. user.py 3. api.py"

ABSOLUTE REQUIREMENTS:
1. EXACTLY ONE SENTENCE - No more, no less (can be as long as needed for clarity)
2. FORBIDDEN SYMBOLS: Never use "1." "2." "3." "a." "b." "c." "-" "•" ":" "："
3. REQUIRED: Describe in ABSTRACT TERMS - general purpose, scope, and outcome only
   (NOT specific items like filenames, file paths, or individual list items)
4. FORBIDDEN STRUCTURE: Never enumerate items one by one
5. Use professional conversational tone: 〜ました、〜しています
6. Keep technical terms in English
7. Follow the GOOD example style: natural narrative, not enumeration
8. Be CONCISE but COMPLETE - don't sacrifice clarity for brevity

Output ONLY ONE COMPLETE SENTENCE."""

# Test scenarios (English + Chinese mix)
TEST_SCENARIOS = [
    "The server is ready for testing and all endpoints are operational.",
    "用戶要求下載新模型並進行比較測試。",
    "I've completed the authentication refactoring. The changes include migrating from sessions to JWT tokens, upgrading password hashing to bcrypt, and adding rate limiting middleware.",
    "已完成模型比较测试。测试了 5 个模型，使用 plan_b_v2 提示词在 5 个真实场景下进行测试。",
    "Fixed the critical bug in payment processing caused by race conditions during concurrent transactions.",
]

def check_real_chinese_contamination(text: str) -> list:
    """Check for REAL Chinese contamination (not Japanese kanji).

    Focus on specific Chinese words that should be Japanese instead.
    """
    contamination = []

    # Specific Chinese contamination patterns from previous tests
    chinese_words = {
        '用戶': 'ユーザー',
        '用户': 'ユーザー',
        '下載': 'ダウンロード',
        '下载': 'ダウンロード',
        '句子': '文',
        '引擎': 'エンジン',
        '語音': '音声',
        '行为': '行動',
        '不可靠': '信頼性が低い',
        '真実的': '実際の',
        '透過': '通じて',
    }

    for chinese, japanese in chinese_words.items():
        if chinese in text:
            contamination.append(f"{chinese} (should be {japanese})")

    return contamination

async def translate_with_timing(text: str, run_num: int) -> dict:
    """Translate with qwen3:4b-instruct and measure time."""
    client = ollama.AsyncClient()

    messages = [
        {"role": "system", "content": PLAN_B_V2},
        {"role": "user", "content": f"Translate to Japanese (output ONLY Japanese, NO explanations):\n\n{text}"}
    ]

    start_time = time.perf_counter()
    try:
        response = await client.chat(
            model="qwen3:4b-instruct",
            messages=messages,
            options={"temperature": 0.1, "top_p": 0.9}
        )
        elapsed = time.perf_counter() - start_time

        result = response['message']['content'].strip().strip('"').strip('「」')

        # Check quality
        contamination = check_real_chinese_contamination(result)

        # Check for excessive English (error output)
        english_words = len([w for w in result.split() if any(c.isalpha() and ord(c) < 128 for c in w)])
        has_english_error = english_words > 10

        return {
            'success': True,
            'elapsed': elapsed,
            'output': result,
            'chars': len(result),
            'contamination': contamination,
            'has_english_error': has_english_error,
            'run': run_num
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'elapsed': elapsed,
            'error': str(e),
            'run': run_num
        }

async def test_scenario(scenario_idx: int, text: str, runs: int = 5):
    """Test one scenario multiple times."""
    print(f"\n{'='*80}")
    print(f"Scenario {scenario_idx}/5: {text[:60]}...")
    print('='*80)

    scenario_results = []

    for run in range(1, runs + 1):
        print(f"  Run {run}/{runs}...", end=" ", flush=True)
        result = await translate_with_timing(text, run)

        if result['success']:
            scenario_results.append(result)

            status = "✅"
            if result['contamination']:
                status = "❌ 中文殘留"
            elif result['has_english_error']:
                status = "❌ ENGLISH"

            print(f"{status} {result['elapsed']:.2f}s | {result['chars']}ch")
            print(f"     Output: {result['output'][:80]}...")

            if result['contamination']:
                print(f"     ⚠️  Contamination: {result['contamination']}")
        else:
            print(f"❌ Error: {result['error']}")

        await asyncio.sleep(0.5)

    # Scenario summary
    if scenario_results:
        times = [r['elapsed'] for r in scenario_results]
        avg = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0

        clean_count = sum(1 for r in scenario_results if not r['contamination'] and not r['has_english_error'])

        print(f"\n  Scenario summary:")
        print(f"    Avg time: {avg:.2f}s ± {std:.2f}s")
        print(f"    Clean outputs: {clean_count}/{len(scenario_results)}")

    return scenario_results

async def main():
    print("="*80)
    print("STABILITY TEST: qwen3:4b-instruct")
    print("="*80)
    print(f"\nModel: qwen3:4b-instruct (no thinking output)")
    print(f"Testing: {len(TEST_SCENARIOS)} scenarios × 5 runs = 25 translations")
    print()

    all_results = []

    for idx, scenario in enumerate(TEST_SCENARIOS, 1):
        results = await test_scenario(idx, scenario, runs=5)
        all_results.extend(results)
        await asyncio.sleep(1)

    # Final analysis
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print('='*80)

    if all_results:
        times = [r['elapsed'] for r in all_results]
        chars = [r['chars'] for r in all_results]

        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)

        avg_chars = statistics.mean(chars)
        std_chars = statistics.stdev(chars) if len(chars) > 1 else 0

        clean_count = sum(1 for r in all_results if not r['contamination'] and not r['has_english_error'])
        contamination_count = sum(1 for r in all_results if r['contamination'])
        english_error_count = sum(1 for r in all_results if r['has_english_error'])

        print(f"\n📊 Performance:")
        print(f"   Total runs: {len(all_results)}")
        print(f"   Average time: {avg_time:.2f}s ± {std_time:.2f}s")
        print(f"   Min time: {min_time:.2f}s")
        print(f"   Max time: {max_time:.2f}s")

        print(f"\n📝 Quality:")
        print(f"   Clean outputs: {clean_count}/{len(all_results)} ({clean_count/len(all_results)*100:.0f}%)")
        print(f"   Chinese contamination: {contamination_count}/{len(all_results)} ({contamination_count/len(all_results)*100:.0f}%)")
        print(f"   English errors: {english_error_count}/{len(all_results)} ({english_error_count/len(all_results)*100:.0f}%)")
        print(f"   Avg output length: {avg_chars:.1f} ± {std_chars:.1f} chars")

        print(f"\n📈 Stability:")
        print(f"   Time variance (σ): {std_time:.2f}s")
        if std_time < 1.0:
            print(f"   ✅ EXCELLENT stability (σ < 1.0s)")
        elif std_time < 2.0:
            print(f"   ✅ GOOD stability (σ < 2.0s)")
        else:
            print(f"   ⚠️  MODERATE stability (σ ≥ 2.0s)")

        print(f"\n{'='*80}")
        if clean_count >= 23:  # 92% clean rate
            print(f"✅ PASSED: {clean_count/len(all_results)*100:.0f}% clean outputs")
            print(f"   Average speed: {avg_time:.2f}s")
            print(f"   Stability: σ={std_time:.2f}s")
            print(f"   Recommendation: UPGRADE to qwen3:4b-instruct")
        elif clean_count >= 20:  # 80% clean rate
            print(f"⚠️  ACCEPTABLE: {clean_count/len(all_results)*100:.0f}% clean outputs")
            print(f"   May proceed with caution")
        else:
            print(f"❌ FAILED: Only {clean_count/len(all_results)*100:.0f}% clean outputs")
            print(f"   DO NOT upgrade")
        print('='*80)

if __name__ == "__main__":
    asyncio.run(main())
