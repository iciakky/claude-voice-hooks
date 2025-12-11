"""Mock objects for testing."""

from .mock_ollama import (
    MockOllamaClient,
    MockOllamaProvider,
    create_mock_ollama_warmup,
    create_mock_ollama_failure
)

__all__ = [
    'MockOllamaClient',
    'MockOllamaProvider',
    'create_mock_ollama_warmup',
    'create_mock_ollama_failure'
]
