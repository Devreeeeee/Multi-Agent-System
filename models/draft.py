"""
Draft dataclass — represents one version of the Writer's output.
"""
from dataclasses import dataclass, field
from datetime import datetim


@dataclass
class Draft:
    """A versioned document produced (or revised) by the WriterAgent."""

    content: str
    revision_number: int = 0
    created_at: datetime = field(default_factory=datetime.now)
