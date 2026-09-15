"""
PlannerAgent — breaks a user topic into 2–4 independent sub-tasks.
"""
from __future__ import annotations

import re

from multi_agent_system.agents.base_agent import BaseAgent
from multi_agent_system.exceptions import PlannerFailedError
from multi_agent_system.models.log_entry import IntermediateLog
from multi_agent_system.models.subtask import SubTask
from multi_agent_system.prompts.planner_prompt import build_planner_prompt

# Maximum sub-tasks the Planner may return
_MAX_SUBTASKS = 4
# Minimum sub-tasks required
_MIN_SUBTASKS = 1


class PlannerAgent(BaseAgent):
    """Decomposes a research topic into a short, ordered list of sub-tasks."""

    def __init__(self, logs: list[IntermediateLog]) -> None:
        super().__init__(logs)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, topic: str) -> list[SubTask]:  # type: ignore[override]
        """
        Break *topic* into sub-tasks.

        Parameters
        ----------
        topic:
            The validated, stripped user-supplied research topic.

        Returns
        -------
        list[SubTask]
            Between 1 and 4 SubTask objects with sequential IDs.

        Raises
        ------
        PlannerFailedError
            If no sub-tasks could be extracted from the LLM response.
        """
        prompt = build_planner_prompt(topic)
        raw = self._call_llm(prompt)
        subtasks = self._parse_subtasks(raw)

        if not subtasks:
            raise PlannerFailedError(
                f"PlannerAgent returned no sub-tasks for topic: {topic!r}"
            )

        self._log(
            input_summary=f"Topic: {topic!r}",
            output_summary=f"{len(subtasks)} sub-task(s): "
                           + ", ".join(f"[{st.id}] {st.description[:40]}" for st in subtasks),
        )
        return subtasks

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_subtasks(raw: str) -> list[SubTask]:
        """
        Extract numbered lines from *raw* and build SubTask objects.

        Accepts formats like "1. Foo", "1) Foo", "1 Foo".
        Deduplicates by lowercased description.
        Caps output at _MAX_SUBTASKS.
        """
        seen: set[str] = set()
        subtasks: list[SubTask] = []

        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Match optional leading number + delimiter, then capture the rest
            match = re.match(r"^\d+[.):\s]\s*(.+)$", line)
            if match:
                description = match.group(1).strip()
            else:
                # Accept plain lines too (some LLMs skip the number)
                description = line

            normalised = description.lower()
            if normalised in seen:
                continue
            seen.add(normalised)

            subtasks.append(SubTask(id=len(subtasks) + 1, description=description))
            if len(subtasks) >= _MAX_SUBTASKS:
                break

        return subtasks

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------

    def _mock_response(self) -> str:
        return (
            "1. Define the core concepts and history\n"
            "2. Explore current applications and use cases\n"
            "3. Identify key challenges and limitations\n"
            "4. Summarise future outlook and research directions"
        )
