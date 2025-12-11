"""
Configuration module for Claude Voice Hooks server.

Handles loading, validation, and management of server configuration from:
1. YAML configuration files
2. Environment variables (override)
3. Default values (fallback)

Configuration Structure:
    server:
        host: Server binding address
        port: Server port number
    audio_selector:
        type: Audio selection strategy (classification/random)
        audio_dir: Directory containing audio files
    model_provider:
        type: Model provider (ollama/claude)
        ollama/claude: Provider-specific configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Default configuration values
DEFAULT_CONFIG = {
    "server": {
        "host": "127.0.0.1",
        "port": 8765
    },
    "audio_selector": {
        "type": "classification",
        "audio_dir": str(Path(__file__).parent.parent / "audio"),
        "min_interval": 1.5,
        "max_age_hours": 24,
        "max_size_mb": 500
    },
    "model_provider": {
        "type": "ollama",
        "ollama": {
            "model": "7shi/llama-translate:8b-q4_K_M",
            "base_url": "http://localhost:11434",
            "timeout": 30
        }
    }
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable overrides.

    Args:
        config_path: Path to YAML configuration file.
                     If None, uses default configuration.

    Returns:
        Dictionary containing merged configuration from:
        1. Default values
        2. YAML file (if provided)
        3. Environment variables (highest priority)

    Raises:
        FileNotFoundError: If config_path is provided but file doesn't exist
        yaml.YAMLError: If YAML file is malformed
        ValueError: If configuration validation fails

    Environment Variables:
        SERVER_HOST: Override server.host
        SERVER_PORT: Override server.port
        AUDIO_DIR: Override audio_selector.audio_dir
        MODEL_PROVIDER: Override model_provider.type
        OLLAMA_MODEL: Override model_provider.ollama.model
        OLLAMA_BASE_URL: Override model_provider.ollama.base_url
    """
    # Start with default configuration
    config = _deep_copy_dict(DEFAULT_CONFIG)

    # Load from YAML file if provided
    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config = _deep_merge_dicts(config, yaml_config)
                    logger.info(f"Loaded configuration from {config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}")

    # Apply environment variable overrides
    config = _apply_env_overrides(config)

    # Validate configuration
    validate_config(config)

    logger.debug(f"Final configuration: {config}")
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate required top-level keys
    required_keys = ["server", "audio_selector", "model_provider"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration section: {key}")

    # Validate server configuration
    server = config["server"]
    if "port" in server:
        port = server["port"]
        if not isinstance(port, int) or port < 1024 or port > 65535:
            raise ValueError(f"Invalid port number: {port}. Must be between 1024-65535")

    # Validate audio directory exists
    audio_config = config["audio_selector"]
    if "audio_dir" in audio_config:
        audio_dir = Path(audio_config["audio_dir"])
        if not audio_dir.exists():
            logger.warning(f"Audio directory does not exist: {audio_dir}")
            # Note: Not raising error to allow creation later

    # Validate model provider
    model_config = config["model_provider"]
    valid_providers = ["ollama", "claude"]
    provider_type = model_config.get("type")

    if provider_type not in valid_providers:
        raise ValueError(
            f"Invalid model provider: {provider_type}. "
            f"Must be one of: {valid_providers}"
        )

    # Validate provider-specific configuration
    if provider_type == "ollama":
        if "ollama" not in model_config:
            raise ValueError("Missing 'ollama' configuration for ollama provider")
        if "model" not in model_config["ollama"]:
            raise ValueError("Missing 'model' in ollama configuration")

    elif provider_type == "claude":
        if "claude" not in model_config:
            raise ValueError("Missing 'claude' configuration for claude provider")
        if "api_key" not in model_config["claude"]:
            raise ValueError("Missing 'api_key' in claude configuration")
        if "model" not in model_config["claude"]:
            raise ValueError("Missing 'model' in claude configuration")


def get_audio_directory(config: Dict[str, Any]) -> Path:
    """
    Extract and return audio directory path from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Path object pointing to audio directory
    """
    audio_dir_str = config["audio_selector"]["audio_dir"]
    return Path(audio_dir_str)


def get_model_config(config: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """
    Extract model provider configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (provider_type, provider_config)
        Example: ("ollama", {"model": "gemma3n:e4b", "base_url": "..."})
    """
    model_config = config["model_provider"]
    provider_type = model_config["type"]
    provider_config = model_config.get(provider_type, {})
    return provider_type, provider_config


def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve environment variable references in configuration values.

    Replaces ${VAR_NAME} patterns with actual environment variable values.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with environment variables resolved
    """
    import re

    def resolve_value(value):
        if isinstance(value, str):
            # Find ${VAR} patterns and replace with env var values
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, value)
            for var_name in matches:
                env_value = os.getenv(var_name, '')
                value = value.replace(f'${{{var_name}}}', env_value)
            return value
        elif isinstance(value, dict):
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_value(item) for item in value]
        else:
            return value

    return resolve_value(config)


# Private helper functions

def _deep_copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Deep copy a dictionary."""
    import copy
    return copy.deepcopy(d)


def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary
    """
    result = _deep_copy_dict(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.

    Args:
        config: Base configuration

    Returns:
        Configuration with environment variable overrides applied
    """
    # Server overrides
    if "SERVER_HOST" in os.environ:
        config["server"]["host"] = os.environ["SERVER_HOST"]

    if "SERVER_PORT" in os.environ:
        try:
            config["server"]["port"] = int(os.environ["SERVER_PORT"])
        except ValueError:
            logger.warning(f"Invalid SERVER_PORT value: {os.environ['SERVER_PORT']}")

    # Audio selector overrides
    if "AUDIO_DIR" in os.environ:
        config["audio_selector"]["audio_dir"] = os.environ["AUDIO_DIR"]

    # Model provider overrides
    if "MODEL_PROVIDER" in os.environ:
        config["model_provider"]["type"] = os.environ["MODEL_PROVIDER"]

    if "OLLAMA_MODEL" in os.environ:
        if "ollama" not in config["model_provider"]:
            config["model_provider"]["ollama"] = {}
        config["model_provider"]["ollama"]["model"] = os.environ["OLLAMA_MODEL"]

    if "OLLAMA_BASE_URL" in os.environ:
        if "ollama" not in config["model_provider"]:
            config["model_provider"]["ollama"] = {}
        config["model_provider"]["ollama"]["base_url"] = os.environ["OLLAMA_BASE_URL"]

    return config


# Module-level cached configuration (optional optimization)
_cached_config: Optional[Dict[str, Any]] = None


def get_cached_config() -> Optional[Dict[str, Any]]:
    """
    Get cached configuration if available.

    Returns:
        Cached configuration or None
    """
    return _cached_config


def set_cached_config(config: Dict[str, Any]) -> None:
    """
    Set cached configuration.

    Args:
        config: Configuration to cache
    """
    global _cached_config
    _cached_config = config


def clear_cached_config() -> None:
    """Clear cached configuration."""
    global _cached_config
    _cached_config = None
