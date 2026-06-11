"""
Image Generator Agent — creates prompts for image generation APIs (DALL-E, Stable Diffusion).
Reads prompt from packages/prompts/image/image-illustration.prompt.md
"""
from typing import Optional


async def generate_image_options(activity: dict, profile: dict, openai_key: Optional[str] = None) -> list[dict]:
    title = activity.get("title", "Atividade")
    avoid_visual = "muitas cores simultâneas" in (profile.get("resources_to_avoid") or [])
    style = "minimal, neutral background" if avoid_visual else "colorful, child-friendly"

    return [
        {
            "id": "img_1",
            "description": f"Ilustração principal para '{title}' — fundo neutro, elementos grandes e claros",
            "prompt": f"Simple educational illustration for '{title}', {style}, large clear elements, no text, white background",
            "source": "mock",
        },
        {
            "id": "img_2",
            "description": "Pictogramas AAC para os elementos principais da atividade",
            "prompt": f"AAC-style pictograms for '{title}', simple icons, white background, clear outlines",
            "source": "mock",
        },
    ]
