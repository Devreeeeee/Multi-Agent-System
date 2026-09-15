"""
Prompt templates for the ResearcherAgent.
"""


def build_researcher_prompt(subtask_description: str) -> str:
    return (
        "You are a concise research assistant.\n"
        "Write a short, factual summary (2 to 3 paragraphs) for the following research sub-task.\n\n"
        f"Sub-task: {subtask_description}\n\n"
        "Respond with only the summary text. No headings, no bullet points, no extra commentary."
    )
