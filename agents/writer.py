"""
WriterAgent — composes and revises a structured Markdown document.
"""
from __future__ import annotations

from multi_agent_system.agents.base_agent import BaseAgent
from multi_agent_system.exceptions import WriterFailedError
from multi_agent_system.models.draft import Draft
from multi_agent_system.models.log_entry import IntermediateLog
from multi_agent_system.models.subtask import SubTask
from multi_agent_system.prompts.writer_prompt import build_revise_prompt, build_write_prompt


class WriterAgent(BaseAgent):
    """Produces the initial draft and applies Reviewer-requested revisions."""

    def __init__(self, logs: list[IntermediateLog]) -> None:
        super().__init__(logs)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, subtasks: list[SubTask]) -> Draft:  # type: ignore[override]
        """
        Compose the initial Markdown draft from research summaries.

        Parameters
        ----------
        subtasks:
            SubTask list with research_summary filled in by ResearcherAgent.

        Returns
        -------
        Draft
            The initial document (revision_number = 0).

        Raises
        ------
        WriterFailedError
            If the LLM returns an empty or whitespace-only response.
        """
        prompt = build_write_prompt(subtasks)
        content = self._call_llm(prompt).strip()

        if not content:
            raise WriterFailedError("WriterAgent returned an empty draft.")

        draft = Draft(content=content, revision_number=0)
        self._log(
            input_summary=f"{len(subtasks)} sub-task(s) -> initial draft",
            output_summary=f"Draft v0: {len(content)} characters",
        )
        return draft

    def revise(self, draft: Draft, feedback: str) -> Draft:
        """
        Produce a revised draft incorporating the Reviewer's feedback.

        Parameters
        ----------
        draft:
            The current draft to be improved.
        feedback:
            Specific revision notes from the ReviewerAgent.

        Returns
        -------
        Draft
            A new Draft with revision_number incremented by 1.

        Raises
        ------
        WriterFailedError
            If the LLM returns an empty or whitespace-only response.
        """
        prompt = build_revise_prompt(draft.content, feedback)
        content = self._call_llm(prompt).strip()

        if not content:
            raise WriterFailedError("WriterAgent returned an empty revision.")

        new_draft = Draft(content=content, revision_number=draft.revision_number + 1)
        self._log(
            input_summary=f"Revising draft v{draft.revision_number} - feedback: {feedback[:60]}",
            output_summary=f"Draft v{new_draft.revision_number}: {len(content)} characters",
        )
        return new_draft

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------

    def _mock_response(self) -> str:
        return (
            "# Research Report\n\n"
            "## Introduction\n\n"
            "This report synthesises research across the identified sub-tasks.\n\n"
            "## Core Concepts and History\n\n"
            "This is a mock summary for the first section.\n\n"
            "## Current Applications\n\n"
            "This is a mock summary for the second section.\n\n"
            "## Conclusion\n\n"
            "In conclusion, this topic has significant depth and ongoing relevance."
        )
