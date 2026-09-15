"""
Orchestrator — wires all agents together and manages the revision loop.

The Orchestrator is the sole coordinator: no agent calls another agent
directly. All data flows through here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import multi_agent_system.config as config
from multi_agent_system.agents.planner import PlannerAgent
from multi_agent_system.agents.researcher import ResearcherAgent
from multi_agent_system.agents.reviewer import ReviewerAgent
from multi_agent_system.agents.writer import WriterAgent
from multi_agent_system.exceptions import (
    EmptyTopicError,
    PipelineAbortedError,
    TopicTooLongError,
)
from multi_agent_system.models.draft import Draft
from multi_agent_system.models.log_entry import IntermediateLog
from multi_agent_system.models.review import ReviewDecision
from multi_agent_system.models.subtask import SubTask


@dataclass
class PipelineResult:
    """All outputs produced by a complete Orchestrator run."""

    topic: str
    subtasks: list[SubTask]
    final_draft: Draft
    revision_count: int
    approved_by_reviewer: bool   # False if max-revisions cap was hit
    logs: list[IntermediateLog] = field(default_factory=list)


class Orchestrator:
    """
    Coordinates the four-agent pipeline in strict sequence:

        Planner → Researcher → Writer ↔ Reviewer (revision loop) → Result

    Usage
    -----
    ::

        orchestrator = Orchestrator()
        result = orchestrator.run("The history of quantum computing")
    """

    def __init__(self) -> None:
        # Shared log list — all agents append to this same object
        self._logs: list[IntermediateLog] = []

        self._planner = PlannerAgent(self._logs)
        self._researcher = ResearcherAgent(self._logs)
        self._writer = WriterAgent(self._logs)
        self._reviewer = ReviewerAgent(self._logs)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, topic: str) -> PipelineResult:
        """
        Execute the full agent pipeline for *topic*.

        Parameters
        ----------
        topic:
            Raw user-supplied string. Validation is performed here.

        Returns
        -------
        PipelineResult

        Raises
        ------
        EmptyTopicError
            If *topic* is blank or too short.
        TopicTooLongError
            If *topic* exceeds TOPIC_MAX_LENGTH.
        PipelineAbortedError
            If a fatal agent failure prevents the pipeline from continuing.
        """
        topic = self._validate_topic(topic)

        # ── Stage 1: Plan ─────────────────────────────────────────────
        try:
            subtasks: list[SubTask] = self._planner.run(topic)
        except Exception as exc:
            raise PipelineAbortedError(
                f"Planning stage failed: {exc}"
            ) from exc

        # ── Stage 2: Research ─────────────────────────────────────────
        # ResearcherAgent handles per-subtask failures internally;
        # a total failure would only occur on an unexpected exception.
        try:
            subtasks = self._researcher.run(subtasks)
        except Exception as exc:
            raise PipelineAbortedError(
                f"Research stage failed: {exc}"
            ) from exc

        # ── Stage 3: Write (initial draft) ────────────────────────────
        try:
            draft: Draft = self._writer.run(subtasks)
        except Exception as exc:
            raise PipelineAbortedError(
                f"Writing stage failed: {exc}"
            ) from exc

        # ── Stage 4: Review / revise loop ─────────────────────────────
        revision_count = 0
        decision: ReviewDecision | None = None

        while True:
            try:
                decision = self._reviewer.run(draft, revision_count)
            except Exception as exc:
                raise PipelineAbortedError(
                    f"Review stage failed: {exc}"
                ) from exc

            if decision.approved:
                break

            # Revision requested — ask Writer to improve
            revision_count += 1
            try:
                draft = self._writer.revise(draft, decision.feedback)
            except Exception as exc:
                raise PipelineAbortedError(
                    f"Revision stage failed: {exc}"
                ) from exc

        approved_by_reviewer = (
            decision.approved
            and revision_count < config.MAX_REVISIONS
        )

        return PipelineResult(
            topic=topic,
            subtasks=subtasks,
            final_draft=draft,
            revision_count=revision_count,
            approved_by_reviewer=approved_by_reviewer,
            logs=list(self._logs),  # snapshot
        )

    def get_logs(self) -> list[IntermediateLog]:
        """Return all accumulated intermediate logs."""
        return list(self._logs)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_topic(topic: str) -> str:
        """
        Strip whitespace and enforce length constraints.

        Returns the cleaned topic string.

        Raises
        ------
        EmptyTopicError
        TopicTooLongError
        """
        topic = topic.strip()
        if len(topic) < config.TOPIC_MIN_LENGTH:
            raise EmptyTopicError(
                f"Topic must be at least {config.TOPIC_MIN_LENGTH} characters. "
                f"Got: {topic!r}"
            )
        if len(topic) > config.TOPIC_MAX_LENGTH:
            raise TopicTooLongError(
                f"Topic must be at most {config.TOPIC_MAX_LENGTH} characters. "
                f"Got {len(topic)} characters."
            )
        return topic
