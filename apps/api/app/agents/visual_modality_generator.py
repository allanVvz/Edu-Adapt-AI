"""
Visual Modality Generator — creates card/column visual layout structure.
Reads prompt from packages/prompts/visual/visual-activity.prompt.md
"""


async def generate_visual_modality(activity: dict, profile: dict) -> dict:
    return {
        "type": "card_columns",
        "title": activity.get("title", ""),
        "instructions": "OBSERVE E RESPONDA.",
        "columns": [
            {"label": "Água", "items": []},
            {"label": "Terra", "items": []},
        ],
        "print_version": {
            "format": "A4",
            "layout": "two_columns",
            "font_size": "large",
            "high_contrast": True,
            "answer_space": True,
        },
        "source": "mock",
    }
