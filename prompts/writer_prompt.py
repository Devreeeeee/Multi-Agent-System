"""
Prompt templates for the WriterAgent.
"""
from __future__ import annotations

from multi_agent_system.models.subtask import SubTask


def build_write_prompt(subtasks: list[SubTask]) -> str:
    sections = "\n\n".join(
        f"Sub-task {st.id}: {st.description}\nSummary: {st.research_summary or 'No information available.'}"
        for st in subtasks
    )
    return (
        "You are a professional technical writer.\n"
        "Using the research summaries below, write a well-structured Markdown document.\n"
        "The document must include:\n"
        "  - A top-level title (# ...)\n"
        "  - A brief introduction paragraph\n"
        "  - One ## section per sub-task, using its description as the heading\n"
        "  - A conclusion paragraph\n\n"
        "Research summaries:\n"
        f"{sections}\n\n"
        "Write only the Markdown document. No preamble, no commentary."
    )


def build_revise_prompt(draft_content: str, feedback: str) -> str:
    return (
        "You are a professional technical writer.\n"
        "Revise the Markdown document below based on the specific feedback provided.\n"
        "Only change what the feedback identifies. Keep everything else intact.\n\n"
        f"Feedback:\n{feedback}\n\n"
        f"Current document:\n{draft_content}\n\n"
        "Return only the revised Markdown document."
    )
