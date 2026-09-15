"""
ResearcherAgent — produces a short summary for each sub-task.
"""
from __future__ import annotations

from multi_agent_system.agents.base_agent import BaseAgent
from multi_agent_system.models.log_entry import IntermediateLog
from multi_agent_system.models.subtask import SubTask
from multi_agent_system.prompts.researcher_prompt import build_researcher_prompt

_SKIPPED_PLACEHOLDER = "No information found for this sub-task."


class ResearcherAgent(BaseAgent):
    """Fills in research_summary on every SubTask, one LLM call per sub-task."""

    def __init__(self, logs: list[IntermediateLog]) -> None:
        super().__init__(logs)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, subtasks: list[SubTask]) -> list[SubTask]:  # type: ignore[override]
        """
        Populate research_summary on each SubTask.

        A failure on any individual sub-task marks it SKIPPED with a
        placeholder — the loop continues rather than aborting.

        Parameters
        ----------
        subtasks:
            The list produced by PlannerAgent (mutated in place).

        Returns
        -------
        list[SubTask]
            The same list with research_summary filled in.
        """
        researched = 0
        skipped = 0

        for subtask in subtasks:
            try:
                prompt = build_researcher_prompt(subtask.description)
                summary = self._call_llm(prompt).strip()
                if not summary:
                    raise ValueError("LLM returned an empty summary.")
                subtask.research_summary = summary
                subtask.status = "RESEARCHED"
                researched += 1
            except Exception as exc:  # noqa: BLE001 — per-item isolation
                subtask.research_summary = _SKIPPED_PLACEHOLDER
                subtask.status = "SKIPPED"
                skipped += 1
                # Log the individual failure but don't crash
                import logging
                logging.getLogger(__name__).warning(
                    "ResearcherAgent: sub-task %d skipped — %s", subtask.id, exc
                )

        self._log(
            input_summary=f"{len(subtasks)} sub-task(s) received",
            output_summary=f"{researched} researched, {skipped} skipped",
        )
        return subtasks

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------

    def _mock_response(self) -> str:
        return (
            "This is a concise mock research summary. "
            "It covers the key facts about the sub-task in a clear and structured way. "
            "Additional context and supporting evidence would appear here in a real response."
        )
