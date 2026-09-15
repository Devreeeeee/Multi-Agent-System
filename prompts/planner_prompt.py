"""
Prompt template for the PlannerAgent.
"""


def build_planner_prompt(topic: str) -> str:
    return (
        "You are a research planning assistant.\n"
        "Break the following topic into exactly 2 to 4 focused, independent sub-tasks "
        "that can each be researched separately.\n\n"
        f"Topic: {topic}\n\n"
        "Respond with ONLY a numbered list, one sub-task per line, like:\n"
        "1. Sub-task one\n"
        "2. Sub-task two\n"
        "No introductions, no explanations, no extra text."
    )
