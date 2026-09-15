"""
SubTask dataclass — represents one unit of work from the Planner.
"""
from dataclasses import dataclass, field


@dataclass
class SubTask:
    """A single researchable sub-task produced by the PlannerAgent."""

    id: int
    description: str
    research_summary: str | None = None
    # Possible values: "PENDING", "RESEARCHED", "SKIPPED"
    status: str = field(default="PENDING")
