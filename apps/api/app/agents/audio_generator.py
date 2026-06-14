"""
Audio Generator Agent — creates narration scripts for TTS.

Generates scripts with TEA-specific markers ([pausa], [repete], [aguarda toque])
and includes metadata for OpenAI TTS: voice, rhythm (speed), pitch per profile.
"""
import re
from typing import Optional

_VOICE_STYLE_LABEL = {
    "não verbal":         "grave e muito pausado",
    "nao verbal":         "grave e muito pausado",
    "hipersensibilidade": "pausado e tranquilo",
    "apoio visual":       "claro e objetivo",
    "leitura inicial":    "claro e objetivo",
}

_PROFILE_AUDIO_CONFIG: dict[str, dict] = {
    "não verbal":         {"rhythm": 0.62, "voice": "onyx",    "pitch": "grave"},
    "nao verbal":         {"rhythm": 0.62, "voice": "onyx",    "pitch": "grave"},
    "hipersensibilidade": {"rhythm": 0.80, "voice": "nova",    "pitch": "normal"},
    "apoio visual":       {"rhythm": 0.95, "voice": "shimmer", "pitch": "normal"},
    "leitura inicial":    {"rhythm": 0.95, "voice": "shimmer", "pitch": "normal"},
}

_DEFAULT_AUDIO_CONFIG = {"rhythm": 1.00, "voice": "alloy", "pitch": "normal"}

# Regex that matches all TTS marker tags
_MARKER_RE = re.compile(r'\[(?:pausa|repete|aguarda toque)\]', re.IGNORECASE)


def _strip_tts_markers(script: str) -> str:
    """Remove [pausa], [repete], [aguarda toque] from script before sending to TTS."""
    cleaned = _MARKER_RE.sub(' ', script)
    return re.sub(r' {2,}', ' ', cleaned).strip()


def _get_audio_config(profile_name: str) -> dict:
    name = (profile_name or "").lower()
    for key, cfg in _PROFILE_AUDIO_CONFIG.items():
        if key in name:
            return cfg
    return _DEFAULT_AUDIO_CONFIG


def _get_voice_style_label(profile_name: str) -> str:
    name = (profile_name or "").lower()
    for key, label in _VOICE_STYLE_LABEL.items():
        if key in name:
            return label
    return "direto ao ponto"


def _build_script(statement: str, question: str, profile_name: str) -> str:
    """Build a narration script with TEA-appropriate markers."""
    name = (profile_name or "").lower()

    if "não verbal" in name or "nao verbal" in name:
        # Comunicador Simbólico: 1 palavra-chave + aguarda toque
        keyword = question.split()[0].upper() if question else "RESPONDA"
        return f"{keyword}… [aguarda toque]"

    if "hipersensibilidade" in name:
        # Conector Visual: pausas entre frases
        parts = []
        if statement:
            parts.append(statement)
        if question:
            parts.append(f"[pausa] {question} [pausa]")
        parts.append("[repete]")
        return " ".join(parts)

    if "apoio visual" in name or "leitura inicial" in name:
        # Explorador Verbal: lê 1x, voz clara
        parts = ["Preste atenção."]
        if statement:
            parts.append(statement)
        if question:
            parts.append(f"Agora responda: {question}")
        return "\n\n".join(parts)

    # Padrão
    parts = ["Preste atenção."]
    if statement:
        parts.append(statement)
    if question:
        parts.append(f"Agora responda:\n\n{question}")
    return "\n\n".join(parts)


async def generate_audio_options(
    activity: dict,
    profile: dict,
    openai_key: Optional[str] = None,
) -> list[dict]:
    statement = activity.get("statement", "")
    question = activity.get("question", "")
    profile_name = profile.get("name", "")

    script = _build_script(statement, question, profile_name)
    tts_script = _strip_tts_markers(script)
    cfg = _get_audio_config(profile_name)
    voice_style = _get_voice_style_label(profile_name)

    return [
        {
            "id": "audio_1",
            "script": script,
            "tts_script": tts_script,
            "voice_style": voice_style,
            "voice": cfg["voice"],
            "rhythm": cfg["rhythm"],
            "pitch": cfg["pitch"],
            "audio_url": None,
            "source": "mock",
        }
    ]
