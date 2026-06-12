"""
Audio Generator Agent — creates narration scripts for TTS.
Adapts voice style based on student autonomy level from profile.
"""
from typing import Optional

_VOICE_MAP = {
    "low": "calmo e pausado, com pausas longas entre as instruções",
    "medium": "claro e objetivo",
    "high": "direto ao ponto",
}


async def generate_audio_options(activity: dict, profile: dict, openai_key: Optional[str] = None) -> list[dict]:
    statement = activity.get("statement", "")
    question = activity.get("question", "")
    autonomy = profile.get("autonomy_level") or "medium"
    voice = _VOICE_MAP.get(autonomy, "claro e objetivo")

    script_parts = ["Preste atenção."]
    if statement:
        script_parts.append(statement)
    if question:
        script_parts.append(f"Agora responda:\n\n{question}")

    return [
        {
            "id": "audio_1",
            "script": "\n\n".join(script_parts),
            "voice_style": voice,
            "source": "mock",
        }
    ]
