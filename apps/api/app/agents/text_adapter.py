"""
Text Adapter Agent — simplifies and adapts the activity text to the student profile.
Uses all available activity and profile fields to produce contextual content.
"""
from typing import Optional


async def adapt_text(activity: dict, profile: dict, openai_key: Optional[str] = None) -> list[dict]:
    statement = activity.get("statement", "")
    question = activity.get("question", "")
    objective = activity.get("pedagogical_objective", "")
    teacher_notes = activity.get("teacher_notes", "")
    discipline = activity.get("discipline", "")
    school_year = activity.get("school_year", "")

    parts = []
    if discipline or school_year:
        ctx = " — ".join(filter(None, [discipline, school_year]))
        parts.append(f"[{ctx}]")
    if objective:
        parts.append(f"Objetivo: {objective}")
    if statement:
        parts.append(statement)
    if question:
        parts.append(question)
    if teacher_notes:
        parts.append(f"Observação: {teacher_notes}")

    adapted = "\n\n".join(parts) if parts else "Observe a atividade."

    reading = profile.get("reading_level", "")
    if reading == "initial":
        adapted = adapted.upper()

    return [{"version": 1, "content": adapted.strip(), "source": "mock"}]
