"""
Orchestrator agent — coordinates all other agents in sequence.
Currently delegates to mock or OpenAI based on available key.
Replace inner calls with real agent invocations as each agent is implemented with AI.
"""
from typing import Optional
from .text_adapter import adapt_text
from .audio_generator import generate_audio_options
from .image_generator import generate_image_options
from .visual_modality_generator import generate_visual_modality
from .interaction_generator import generate_interaction
from .adaptation_validator import validate_adaptation


async def run_adaptation_pipeline(
    activity: dict,
    profile: dict,
    openai_key: Optional[str] = None,
) -> dict:
    text = await adapt_text(activity, profile, openai_key)
    images = await generate_image_options(activity, profile, openai_key)
    audio = await generate_audio_options(activity, profile, openai_key)
    visual = await generate_visual_modality(activity, profile)
    interaction = await generate_interaction(activity, profile)
    validation = await validate_adaptation(text, images, audio, profile)

    return {
        "text_adaptations": text,
        "image_options": images,
        "audio_options": audio,
        "visual_modality": visual,
        "interaction_options": interaction,
        "validation": validation,
    }
