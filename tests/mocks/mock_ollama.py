"""
Mock Ollama responses for testing.
"""
from typing import Dict, Any
from unittest.mock import AsyncMock


class MockOllamaClient:
    """Mock Ollama client for testing without requiring actual Ollama server."""

    def __init__(self, responses: Dict[str, str] = None):
        """
        Initialize mock client.

        Args:
            responses: Dict mapping input text patterns to classification results
                      e.g., {"success": "completion", "error": "failure"}
        """
        self.responses = responses or {
            "success": "completion",
            "completed": "completion",
            "implemented": "completion",
            "done": "completion",
            "error": "failure",
            "failed": "failure",
            "exception": "failure",
            "problem": "failure",
            "permission": "authorization",
            "unauthorized": "authorization",
            "access": "authorization"
        }
        self.call_count = 0
        self.last_request = None

    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Mock generate method that returns classification based on prompt content.

        Args:
            model: Model name (ignored in mock)
            prompt: The prompt text
            **kwargs: Additional arguments (ignored in mock)

        Returns:
            Mock Ollama response
        """
        self.call_count += 1
        self.last_request = {
            "model": model,
            "prompt": prompt,
            "kwargs": kwargs
        }

        # Determine classification based on keywords in prompt
        prompt_lower = prompt.lower()
        classification = "completion"  # Default

        for keyword, intent in self.responses.items():
            if keyword in prompt_lower:
                classification = intent
                break

        return {
            "model": model,
            "created_at": "2025-12-10T12:00:00Z",
            "response": classification,
            "done": True,
            "total_duration": 1500000000,  # 1.5s in nanoseconds
            "load_duration": 500000000,
            "prompt_eval_count": 50,
            "eval_count": 1
        }

    def reset(self):
        """Reset call tracking."""
        self.call_count = 0
        self.last_request = None


class MockOllamaProvider:
    """Mock Model Provider for testing."""

    def __init__(self, default_intent: str = "completion"):
        """
        Initialize mock provider.

        Args:
            default_intent: Default intent to return
        """
        self.default_intent = default_intent
        self.classify_count = 0

    async def classify_intent(self, text: str) -> str:
        """
        Mock classify_intent method.

        Args:
            text: Input text

        Returns:
            Intent classification
        """
        self.classify_count += 1

        # Simple keyword-based mock classification
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ["success", "completed", "implemented", "done"]):
            return "completion"
        elif any(keyword in text_lower for keyword in ["error", "failed", "exception", "problem"]):
            return "failure"
        elif any(keyword in text_lower for keyword in ["permission", "unauthorized", "access"]):
            return "authorization"

        return self.default_intent


def create_mock_ollama_warmup() -> AsyncMock:
    """
    Create a mock function for Ollama model warmup.

    Returns:
        AsyncMock that simulates successful warmup
    """
    async def mock_warmup():
        """Mock warmup that completes instantly."""
        return True

    return AsyncMock(side_effect=mock_warmup)


def create_mock_ollama_failure() -> AsyncMock:
    """
    Create a mock function that simulates Ollama failure.

    Returns:
        AsyncMock that raises exception
    """
    async def mock_failure(*args, **kwargs):
        """Mock failure."""
        raise ConnectionError("Failed to connect to Ollama server")

    return AsyncMock(side_effect=mock_failure)
