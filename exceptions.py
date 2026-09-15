"""
Custom exceptions for the Multi-Agent Research & Content System.
"""


class EmptyTopicError(ValueError):
    """Raised when the user submits a blank or too-short topic."""


class TopicTooLongError(ValueError):
    """Raised when the user submits a topic that exceeds the maximum length."""


class PlannerFailedError(RuntimeError):
    """Raised when the PlannerAgent cannot produce any sub-tasks."""


class ResearcherFailedError(RuntimeError):
    """Raised when a single sub-task research call fails unrecoverably."""


class WriterFailedError(RuntimeError):
    """Raised when the WriterAgent returns empty or malformed content."""


class ReviewerFailedError(RuntimeError):
    """Raised when the ReviewerAgent returns an unparseable response."""


class PipelineAbortedError(RuntimeError):
    """Raised by the Orchestrator when a fatal agent failure stops the pipeline."""


class LLMConnectionError(RuntimeError):
    """Raised when the LLM API (Anthropic) is unreachable or returns an error."""
