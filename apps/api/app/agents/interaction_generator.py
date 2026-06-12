"""
Interaction Generator — creates drag-and-drop / association interactive structure.
Derives items from expected_answer and zones from question using smart parsing.
"""
import re


def _parse_items(answer: str) -> list[str]:
    """Extract items from expected_answer by comma, semicolon, newline or period.

    Removes connective phrases like "são aquáticos", "vivem na água".
    Example: "Peixe, Tubarão são aquáticos. Leão, Elefante são terrestres."
             → ["Peixe", "Tubarão", "Leão", "Elefante"]
    """
    if not answer:
        return []
    # Strip connective phrases before splitting
    cleaned = re.sub(
        r'\s+(são|vivem|pertencem|fazem parte|estão|ficam|habitam|ficam)\s+[\w\s]+?(?=[,.\n]|$)',
        '',
        answer,
        flags=re.IGNORECASE,
    )
    parts = re.split(r'[,;\n.]+', cleaned)
    items = []
    for part in parts:
        part = part.strip()
        if part and 1 < len(part) < 40:
            items.append(part)
    return items[:6]


def _parse_zones(question: str, answer: str) -> list[str]:
    """Extract category zones from the question or answer.

    Looks for patterns: "em X ou Y", "entre X e Y", "para X ou Y".
    Falls back to looking for "são X / são Y" patterns in the answer.
    """
    # Pattern in question: "em X ou Y" / "entre X e Y"
    match = re.search(
        r'\b(?:em|entre|para|no|na|nos|nas)\s+([^,?.\n]+?)\s+(?:ou|e)\s+([^,?.\n]+?)(?:\?|\.|\n|$)',
        question,
        re.IGNORECASE,
    )
    if match:
        z1 = match.group(1).strip().capitalize()
        z2 = match.group(2).strip().capitalize()
        if len(z1) < 30 and len(z2) < 30:
            return [z1, z2]

    # Pattern in answer: "são aquáticos ... são terrestres"
    categories = re.findall(r'(?:são|vivem|pertencem)\s+([\w]+)', answer, re.IGNORECASE)
    seen: list[str] = []
    for cat in categories:
        cap = cat.capitalize()
        if cap not in seen:
            seen.append(cap)
        if len(seen) == 2:
            return seen

    return ["Grupo A", "Grupo B"]


def _build_instructions(question: str) -> str:
    q = question.strip() if question else ""
    if not q:
        return "ARRASTE CADA ITEM PARA O GRUPO CORRETO."
    if q.endswith("?"):
        return q
    return q.upper().rstrip('.') + "."


async def generate_interaction(activity: dict, profile: dict) -> list[dict]:
    question = activity.get("question", "")
    answer = activity.get("expected_answer", "")

    items = _parse_items(answer)
    if not items:
        items = _parse_items(question)
    if not items:
        items = ["Opção 1", "Opção 2"]

    zones = _parse_zones(question, answer)
    instructions = _build_instructions(question)

    return [
        {
            "type": "drag_and_drop",
            "instructions": instructions,
            "items": items,
            "zones": zones,
            "feedback_correct": "Muito bem!",
            "feedback_incorrect": "Tente novamente.",
            "source": "mock",
        }
    ]
