"""
Orchestrator agent — coordinates all other agents in sequence.
With an OpenAI key, delegates to the AI service for the full pipeline.
Without a key, calls each mock agent and assembles the result.
"""
from typing import Optional
from .text_adapter import adapt_text
from .audio_generator import generate_audio_options
from .image_generator import generate_image_options
from .visual_modality_generator import generate_visual_modality
from .interaction_generator import generate_interaction
from .adaptation_validator import validate_adaptation


def _generate_print_version(activity: dict) -> dict:
    return {
        "format": "A4",
        "layout": "single_column",
        "font_size": "large",
        "instructions": (activity.get("question") or "OBSERVE E RESPONDA.").upper(),
        "answer_space": True,
    }


async def run_adaptation_pipeline(
    activity: dict,
    profile: dict,
    openai_key: Optional[str] = None,
) -> dict:
    if openai_key:
        from ..services.openai_service import generate_adaptation_with_ai
        return await generate_adaptation_with_ai(openai_key, activity, profile)

    # Mock pipeline — each agent gets all enriched fields
    text = await adapt_text(activity, profile)
    images = await generate_image_options(activity, profile)
    audio = await generate_audio_options(activity, profile)
    visual = await generate_visual_modality(activity, profile)
    interaction = await generate_interaction(activity, profile)
    validation = await validate_adaptation(text, images, audio, profile)
    print_version = _generate_print_version(activity)

    return {
        "text_adaptations": text,
        "image_options": images,
        "audio_options": audio,
        "visual_modality": visual,
        "interaction_options": interaction,
        "print_version": print_version,
        "validation": validation,
    }
