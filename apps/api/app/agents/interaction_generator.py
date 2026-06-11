"""
Interaction Generator — creates drag-and-drop / association interactive structure.
Reads prompt from packages/prompts/interaction/drag-drop.prompt.md
"""


async def generate_interaction(activity: dict, profile: dict) -> list[dict]:
    answer = activity.get("expected_answer", "")
    items = [s.strip().split(" ")[0] for s in answer.replace(".", ",").split(",") if s.strip()][:4]
    if not items:
        items = ["Item 1", "Item 2"]

    return [
        {
            "type": "drag_and_drop",
            "instructions": "ARRASTE CADA ITEM PARA O LUGAR CERTO.",
            "items": items,
            "zones": ["Água", "Terra"],
            "feedback_correct": "Muito bem!",
            "feedback_incorrect": "Tente novamente.",
            "source": "mock",
        }
    ]
