"""
Central configuration for the Multi-Agent Research & Content System.
"""

# LLM backend: set to True to use stub responses (no API key required)
MOCK_MODE: bool = True

# Anthropic model name (only used when MOCK_MODE is False)
ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

# Maximum revision rounds before the Reviewer is forced to accept
MAX_REVISIONS: int = 2

# Maximum and minimum topic character lengths
TOPIC_MAX_LENGTH: int = 300
TOPIC_MIN_LENGTH: int = 5

# Directory where final Markdown reports are saved
OUTPUT_DIR: str = "output"
