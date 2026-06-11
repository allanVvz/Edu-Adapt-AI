"""
Audio Generator Agent — creates narration scripts for TTS.
Reads prompt from packages/prompts/audio/audio-generation.prompt.md
"""
from typing import Optional


async def generate_audio_options(activity: dict, profile: dict, openai_key: Optional[str] = None) -> list[dict]:
    statement = activity.get("statement", "Observe a atividade.")
    question = activity.get("question", "")
    voice = "calmo e pausado" if profile.get("autonomy_level") == "low" else "claro e objetivo"

    return [
        {
            "id": "audio_1",
            "script": f"Preste atenção.\n\n{statement}\n\nAgora responda:\n\n{question}",
            "voice_style": voice,
            "source": "mock",
        }
    ]
