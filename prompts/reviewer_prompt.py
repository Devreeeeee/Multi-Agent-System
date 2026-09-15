"""
Prompt template for the ReviewerAgent.
"""


def build_reviewer_prompt(draft_content: str) -> str:
    return (
        "You are a strict quality reviewer for research documents.\n"
        "Read the Markdown document below and decide whether it is acceptable.\n\n"
        "Reply with EXACTLY one of:\n"
        "  APPROVED\n"
        "  REVISION NEEDED: <specific, actionable feedback in one sentence>\n\n"
        "No other text.\n\n"
        f"Document:\n{draft_content}"
    )
