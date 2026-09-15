"""
BaseAgent — abstract base class for all agents in the system.

Each concrete agent:
  - Inherits _call_llm() for LLM interaction (real or mock)
  - Overrides _mock_response() to supply its own fake output
  - Calls _log() to append an IntermediateLog entry after each run
"""
from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

import multi_agent_system.config as config
from multi_agent_system.exceptions import LLMConnectionError
from multi_agent_system.models.log_entry import IntermediateLog

if TYPE_CHECKING:
    pass  # avoid circular imports in type stubs

logger = logging.getLogger(__name__)


class BaseAgent(abc.ABC):
    """Abstract base class shared by all four agents."""

    def __init__(self, logs: list[IntermediateLog]) -> None:
        """
        Parameters
        ----------
        logs:
            A shared list owned by the Orchestrator; every agent appends to it.
        """
        self._logs = logs

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        """
        Send *prompt* to the LLM and return the raw text response.

        In mock mode (config.MOCK_MODE is True) the real HTTP call is
        skipped and _mock_response() is returned instead.

        Raises
        ------
        LLMConnectionError
            If the Anthropic API is unreachable or returns a non-success
            status (only raised in real mode).
        """
        if config.MOCK_MODE:
            return self._mock_response()

        # --- Real Anthropic call (requires ANTHROPIC_API_KEY env var) ---
        try:
            import anthropic  # soft import — not required in mock mode

            client = anthropic.Anthropic()
            message = client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text  # type: ignore[index]
        except ImportError as exc:
            raise LLMConnectionError(
                "The 'anthropic' package is not installed. "
                "Run: pip install anthropic"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMConnectionError(
                f"Anthropic API call failed: {exc}"
            ) from exc

    @abc.abstractmethod
    def _mock_response(self) -> str:
        """Return a hardcoded stub response used in mock/test mode."""

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, input_summary: str, output_summary: str) -> None:
        """Append one IntermediateLog entry to the shared log list."""
        entry = IntermediateLog(
            agent_name=self.__class__.__name__,
            input_summary=input_summary,
            output_summary=output_summary,
        )
        self._logs.append(entry)
        logger.debug("[%s] IN: %s | OUT: %s", self.__class__.__name__,
                     input_summary[:80], output_summary[:80])

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def run(self, *args, **kwargs):  # type: ignore[override]
        """Execute the agent's core task. Signature varies per subclass."""
