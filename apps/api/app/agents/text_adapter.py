"""
Text Adapter Agent — simplifies and adapts the activity text to the student profile.
Reads prompt from packages/prompts/text/text-adaptation.prompt.md
"""
from typing import Optional


async def adapt_text(activity: dict, profile: dict, openai_key: Optional[str] = None) -> list[dict]:
    statement = activity.get("statement", "")
    question = activity.get("question", "")

    # Mock adaptation — break into short lines, uppercase key instructions
    adapted = f"OBSERVE A ATIVIDADE.\n\n{statement}\n\n{question}"
    if profile.get("reading_level") == "initial":
        adapted = adapted.upper()

    return [{"version": 1, "content": adapted, "source": "mock"}]
