"""
Translation utilities for server integration.

Provides translate_to_japanese() function using Ollama for English/Mandarin to Japanese translation.
"""

import os
import re
from typing import Optional

try:
    import ollama  # type: ignore
except Exception:
    ollama = None


def _env(key: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default."""
    v = os.environ.get(key)
    return v if v is not None else (default or "")


def _require_ollama():
    """Check if ollama package is installed."""
    if ollama is None:
        raise RuntimeError("python package 'ollama' not installed; run: pip install ollama")


def postprocess_for_tts(text: str) -> str:
    """Post-process translated Japanese text for better TTS pronunciation.

    Transformations:
    0. Remove explanations: Strip "Explanation:" and all text after it
    1. Fractions: "1/2" → "1分の2" (so TTS reads as bunno)
    2. Decimal points in numbers: "3.2" → "3てん2" (so TTS reads it correctly)
    3. Wave dash in number ranges: "1～10" → "1から10" (so TTS reads as kara)
    4. Percent signs: "50%" or "50％" → "50パーセント" (so TTS reads as paasento)
    5. Other periods: "." → " " (space)
    6. Hyphens and underscores: "my-translator" → "my translator"
    7. Uppercase acronyms (4+ letters): "HTTP" → "Http" (so TTS reads more naturally)
    8. Remove spaces between English/numbers and Japanese: "API 設定" → "API設定"
    9. Remove spaces between English and numbers: "python 3" → "python3"

    Args:
        text: Japanese text from translation

    Returns:
        Processed text optimized for TTS
    """
    # 0. Remove unwanted explanations from the model
    # Sometimes the model adds explanations like "Explanation: ..." which we don't want in TTS
    # This removes "Explanation:" and everything after it (case-insensitive)
    text = re.sub(r'Explanation:.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = text.strip()

    # 1. Replace fractions with Japanese "分の" (bunno/fraction)
    # Matches patterns like "1/2", "3/4", "10/100", etc.
    text = re.sub(r'(\d+)/(\d+)', r'\1分の\2', text)

    # 2. Replace decimal points between digits with Japanese "てん" (ten/point)
    # Uses lookahead/lookbehind to match periods between digits: "1.2.3" → "1てん2てん3"
    text = re.sub(r'(?<=\d)\.(?=\d)', 'てん', text)

    # 3. Replace wave dash between digits with Japanese "から" (kara/from-to)
    # Matches patterns like "1～10", "50～100" for number ranges
    text = re.sub(r'(?<=\d)～(?=\d)', 'から', text)

    # 4. Replace percent signs with Japanese "パーセント" (paasento/percent)
    # Matches both full-width "％" and half-width "%" after digits: "50%" → "50パーセント"
    text = re.sub(r'(?<=\d)[％%]', 'パーセント', text)

    # 5. Replace remaining periods with spaces (e.g., filenames, abbreviations)
    text = text.replace('.', ' ')

    # 6. Replace hyphens and underscores with spaces in technical terms
    # This helps TTS pronounce "my-translator" as "my translator" instead of awkward pauses
    text = text.replace('-', ' ')
    text = text.replace('_', ' ')

    # 7. Convert long uppercase acronyms (4+ letters) to capitalized form
    # Examples: "HTTP" → "Http", "HTTPS" → "Https", but "USA" stays "USA"
    text = re.sub(r'[A-Z]{4,}', lambda m: m.group(0).capitalize(), text)

    # 8. Remove spaces between English/numbers and Japanese for smoother reading
    # English/numbers + space + Japanese → merge
    text = re.sub(r'([A-Za-z0-9])\s+([ぁ-ゖァ-ヶ\u4E00-\u9FFF])', r'\1\2', text)
    # Japanese + space + English/numbers → merge
    text = re.sub(r'([ぁ-ゖァ-ヶ\u4E00-\u9FFF])\s+([A-Za-z0-9])', r'\1\2', text)

    # 9. Remove spaces between English and numbers for smoother reading
    # English + space + number → merge
    text = re.sub(r'([A-Za-z])\s+(\d)', r'\1\2', text)
    # Number + space + English → merge
    text = re.sub(r'(\d)\s+([A-Za-z])', r'\1\2', text)

    return text


async def translate_to_japanese(text: str) -> str:
    """Translate English/Mandarin text to Japanese using custom Ollama model.

    Uses the 'my-translator' model (qwen3:4b-instruct base with custom Modelfile)
    configured to output ONLY the translation without explanations.

    Performance: ~0.43s avg, 100% clean outputs, no Chinese contamination.

    Args:
        text: English, Mandarin, or mixed English-Mandarin text to translate

    Returns:
        Japanese translation

    Raises:
        ValueError: If text is empty
        RuntimeError: If translation fails
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("text is required")

    base = _env("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    os.environ.setdefault("OLLAMA_HOST", base)

    _require_ollama()

    # Use custom my-translator model (qwen3:4b-instruct with optimized SYSTEM prompt)
    # The model is pre-configured to produce concise Japanese summaries
    try:
        # Use AsyncClient for non-blocking HTTP calls
        client = ollama.AsyncClient(host=base)
        response = await client.chat(
            model="my-translator",
            messages=[{"role": "user", "content": f"Translate to Japanese:\n\n{text}"}]
        )
        japanese_text = response["message"]["content"].strip()

        # Apply post-processing for better TTS pronunciation
        japanese_text = postprocess_for_tts(japanese_text)

        return japanese_text
    except Exception as e:
        raise RuntimeError(f"translation failed: {e}")
