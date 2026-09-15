"""
ReviewDecision dataclass — represents the Reviewer's verdict on a draft.
"""
from dataclasses import dataclass


@dataclass
class ReviewDecision:
    """The Reviewer's verdict: approved or revision needed."""

    approved: bool
    feedback: str          # empty string when approved=True
    revision_number: int   # which draft revision was reviewed
