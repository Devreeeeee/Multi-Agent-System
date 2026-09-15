"""
IntermediateLog dataclass — transparency record for each agent invocation.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IntermediateLog:
    """A snapshot of one agent's input and output, recorded for transparency."""

    agent_name: str
    input_summary: str
    output_summary: str
    timestamp: datetime = field(default_factory=datetime.now)
