"""
ReviewerAgent — evaluates a draft and returns an approval decision.
"""
from __future__ import annotations

import logging

import multi_agent_system.config as config
from multi_agent_system.agents.base_agent import BaseAgent
from multi_agent_system.models.draft import Draft
from multi_agent_system.models.log_entry import IntermediateLog
from multi_agent_system.models.review import ReviewDecision
from multi_agent_system.prompts.reviewer_prompt import build_reviewer_prompt

logger = logging.getLogger(__name__)

_APPROVED_TOKEN = "APPROVED"
_REVISION_TOKEN = "REVISION NEEDED:"


class ReviewerAgent(BaseAgent):
    """Reads the Writer's draft and decides to approve or request a revision."""

    def __init__(self, logs: list[IntermediateLog]) -> None:
        super().__init__(logs)
        # Internal toggle so the mock alternates approve/reject for testing
        self._mock_call_count: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, draft: Draft, revision_count: int) -> ReviewDecision:  # type: ignore[override]
        """
        Evaluate *draft* and return a ReviewDecision.

        If *revision_count* has already reached MAX_REVISIONS the Reviewer
        automatically approves (forced exit — not an error).

        Parameters
        ----------
        draft:
            The draft to evaluate.
        revision_count:
            How many revision rounds have already occurred.

        Returns
        -------
        ReviewDecision
        """
        # Forced approval when the revision cap has been reached
        if revision_count >= config.MAX_REVISIONS:
            decision = ReviewDecision(
                approved=True,
                feedback="Max revisions reached - accepting current draft.",
                revision_number=draft.revision_number,
            )
            self._log(
                input_summary=f"Draft v{draft.revision_number} (forced accept - max revisions)",
                output_summary="APPROVED (forced)",
            )
            return decision

        prompt = build_reviewer_prompt(draft.content)
        raw = self._call_llm(prompt).strip()
        decision = self._parse_decision(raw, draft.revision_number)

        self._log(
            input_summary=f"Draft v{draft.revision_number}, revision round {revision_count}",
            output_summary=(
                "APPROVED"
                if decision.approved
                else f"REVISION NEEDED: {decision.feedback[:60]}"
            ),
        )
        return decision

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_decision(raw: str, revision_number: int) -> ReviewDecision:
        """
        Parse the LLM response into a ReviewDecision.

        Defaults to approval if the response is unrecognised (to avoid
        getting stuck), and logs a warning.
        """
        if raw.upper().startswith(_APPROVED_TOKEN):
            return ReviewDecision(
                approved=True, feedback="", revision_number=revision_number
            )
        if raw.upper().startswith(_REVISION_TOKEN.upper()):
            feedback = raw[len(_REVISION_TOKEN):].strip()
            return ReviewDecision(
                approved=False,
                feedback=feedback or "The draft needs improvement.",
                revision_number=revision_number,
            )

        # Unrecognised response — default to approved with warning
        logger.warning(
            "ReviewerAgent: unrecognised LLM response %r - defaulting to APPROVED", raw[:80]
        )
        return ReviewDecision(
            approved=True,
            feedback="",
            revision_number=revision_number,
        )

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------

    def _mock_response(self) -> str:
        """
        Alternate between requesting a revision and approving so that mock
        mode exercises the full revision loop during testing.
        """
        self._mock_call_count += 1
        if self._mock_call_count % 2 == 1:
            return "REVISION NEEDED: Add more concrete examples to each section."
        return "APPROVED"
