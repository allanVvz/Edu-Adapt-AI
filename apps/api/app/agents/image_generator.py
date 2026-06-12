"""
Image Generator Agent — creates prompts for image generation APIs (DALL-E, Stable Diffusion).
Respects resources_to_avoid from student profile.
"""
from typing import Optional


async def generate_image_options(activity: dict, profile: dict, openai_key: Optional[str] = None) -> list[dict]:
    title = activity.get("title", "Atividade")
    discipline = activity.get("discipline", "")
    avoid = profile.get("resources_to_avoid") or []
    avoid_str = ", ".join(avoid) if isinstance(avoid, list) else str(avoid)

    avoid_visual_clutter = any(
        kw in avoid_str.lower()
        for kw in ("cor", "muita", "visual", "complexo", "barulho", "texto")
    )
    style = "minimal, neutral background, monochromatic" if avoid_visual_clutter else "colorful, child-friendly"
    context = f"{title}{', ' + discipline if discipline else ''}"

    return [
        {
            "id": "img_1",
            "description": f"Ilustração principal para '{context}' — elementos grandes e claros",
            "prompt": f"Simple educational illustration for '{context}', {style}, large clear elements, no text, white background",
            "source": "mock",
        },
        {
            "id": "img_2",
            "description": f"Pictogramas AAC para os elementos de '{context}'",
            "prompt": f"AAC-style pictograms for '{context}', simple icons, white background, clear outlines, no text",
            "source": "mock",
        },
    ]
