"""
Adaptation Validator — evaluates quality of generated adaptation.
Reads prompt from packages/prompts/validation/adaptation-validation.prompt.md
"""


async def validate_adaptation(text: list, images: list, audio: list, profile: dict) -> dict:
    clarity = 4 if text else 2
    accessibility = 4 if images and audio else 3
    pedagogical = 5

    approved = clarity >= 3 and accessibility >= 3

    return {
        "clarity_score": clarity,
        "accessibility_score": accessibility,
        "pedagogical_score": pedagogical,
        "difficulty_score": 3,
        "approved": approved,
        "notes": "Adaptação gerada por mock. Revise antes de publicar." if not approved else "Adaptação aprovada automaticamente pelo validador mock.",
        "generated_by": "mock",
    }
