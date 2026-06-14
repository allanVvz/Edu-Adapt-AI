"""
Tests for audio generation pipeline.

Unit tests: all OpenAI TTS calls are mocked — no real API keys required.
E2E test: requires OPENAI_TEST_API_KEY env var — calls the real OpenAI TTS API.
"""
import asyncio
import os
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.audio_generator import (
    generate_audio_options,
    _strip_tts_markers,
    _get_audio_config,
)
from app.models.activity import Activity
from app.models.adaptation import ActivityAdaptation
from app.models.api_key import ApiKey
from app.services.openai_service import _mock_adaptation, generate_audio_tts
from .conftest import create_user, get_token, auth

# ─── Test data ────────────────────────────────────────────────────────────────

ACTIVITY = {
    "title": "Interpretar texto curto",
    "statement": "A horta tem alface e tomate.",
    "question": "O que as crianças regam?",
}

PROFILE_NAO_VERBAL = {"name": "TEA — Não Verbal", "autonomy_level": "low"}
PROFILE_HIPER = {"name": "TEA — Hipersensibilidade Visual", "autonomy_level": "medium"}
PROFILE_APOIO = {"name": "TEA — Apoio Visual e Leitura Inicial", "autonomy_level": "low"}
PROFILE_PADRAO = {"name": "Padrão", "autonomy_level": "high"}


# ─── Unit: script structure ───────────────────────────────────────────────────

def test_audio_options_include_rhythm_and_voice():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_NAO_VERBAL))
    assert len(result) >= 1
    opt = result[0]
    assert "rhythm" in opt
    assert "voice" in opt
    assert "tts_script" in opt
    assert "script" in opt
    assert "audio_url" in opt


def test_comunicador_simbolico_gets_slowest_rhythm():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_NAO_VERBAL))
    assert result[0]["rhythm"] == 0.62


def test_conector_visual_gets_medium_rhythm():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_HIPER))
    assert result[0]["rhythm"] == 0.80


def test_explorador_verbal_gets_fast_rhythm():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_APOIO))
    assert result[0]["rhythm"] == 0.95


def test_padrao_gets_full_speed_rhythm():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_PADRAO))
    assert result[0]["rhythm"] == 1.00


def test_comunicador_simbolico_script_has_aguarda_toque():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_NAO_VERBAL))
    assert "[aguarda toque]" in result[0]["script"]


def test_conector_visual_script_has_pausa():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_HIPER))
    assert "[pausa]" in result[0]["script"]


def test_comunicador_simbolico_voice_is_onyx():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_NAO_VERBAL))
    assert result[0]["voice"] == "onyx"


def test_conector_visual_voice_is_nova():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_HIPER))
    assert result[0]["voice"] == "nova"


def test_explorador_verbal_voice_is_shimmer():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_APOIO))
    assert result[0]["voice"] == "shimmer"


# ─── Unit: _strip_tts_markers ─────────────────────────────────────────────────

def test_strip_tts_markers_removes_aguarda_toque():
    cleaned = _strip_tts_markers("ALFACE… [aguarda toque]")
    assert "[aguarda toque]" not in cleaned
    assert "ALFACE" in cleaned


def test_strip_tts_markers_removes_pausa():
    cleaned = _strip_tts_markers("frase [pausa] outra frase")
    assert "[pausa]" not in cleaned


def test_strip_tts_markers_removes_repete():
    cleaned = _strip_tts_markers("instrução [repete]")
    assert "[repete]" not in cleaned


def test_strip_tts_markers_preserves_content():
    cleaned = _strip_tts_markers("Olá [pausa] mundo [repete] fim")
    assert "Olá" in cleaned
    assert "mundo" in cleaned
    assert "fim" in cleaned


def test_tts_script_field_has_no_markers():
    result = asyncio.run(generate_audio_options(ACTIVITY, PROFILE_NAO_VERBAL))
    tts = result[0]["tts_script"]
    assert "[aguarda toque]" not in tts
    assert "[pausa]" not in tts
    assert "[repete]" not in tts


# ─── Unit: _get_audio_config ──────────────────────────────────────────────────

def test_get_audio_config_nao_verbal():
    cfg = _get_audio_config("TEA — Não Verbal")
    assert cfg["rhythm"] == 0.62
    assert cfg["voice"] == "onyx"


def test_get_audio_config_hiper():
    cfg = _get_audio_config("TEA — Hipersensibilidade Visual")
    assert cfg["rhythm"] == 0.80
    assert cfg["voice"] == "nova"


def test_get_audio_config_apoio():
    cfg = _get_audio_config("TEA — Apoio Visual e Leitura Inicial")
    assert cfg["rhythm"] == 0.95
    assert cfg["voice"] == "shimmer"


def test_get_audio_config_unknown_returns_default():
    cfg = _get_audio_config("Perfil Desconhecido")
    assert cfg["rhythm"] == 1.00
    assert cfg["voice"] == "alloy"


# ─── Unit: generate_audio_tts (mocked) ────────────────────────────────────────

@pytest.fixture
def mock_tts():
    fake_response = MagicMock()
    fake_response.content = b"ID3" + b"\x00" * 200
    with patch("openai.AsyncOpenAI") as mock_cls:
        instance = MagicMock()
        instance.audio.speech.create = AsyncMock(return_value=fake_response)
        mock_cls.return_value = instance
        yield mock_cls


def test_generate_audio_tts_returns_url(mock_tts, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.openai_service._AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.openai_service._API_BASE_URL", "http://test")
    url = asyncio.run(generate_audio_tts("sk-fake", "Texto de teste", "alloy", 1.0))
    assert url.startswith("http://test/static/audio/")
    assert url.endswith(".mp3")


def test_generate_audio_tts_saves_file(mock_tts, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.openai_service._AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.openai_service._API_BASE_URL", "http://test")
    url = asyncio.run(generate_audio_tts("sk-fake", "Texto de teste", "alloy", 1.0))
    filename = url.split("/")[-1]
    assert (tmp_path / filename).exists()
    assert (tmp_path / filename).stat().st_size > 0


def test_generate_audio_tts_clamps_speed_low(mock_tts, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.openai_service._AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.openai_service._API_BASE_URL", "http://test")
    asyncio.run(generate_audio_tts("sk-fake", "texto", "alloy", speed=0.1))  # clamped to 0.25


def test_generate_audio_tts_clamps_speed_high(mock_tts, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.openai_service._AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.openai_service._API_BASE_URL", "http://test")
    asyncio.run(generate_audio_tts("sk-fake", "texto", "alloy", speed=10.0))  # clamped to 4.0


# ─── Integration: generate-audio endpoint ─────────────────────────────────────

def _seed_adaptation_with_audio_key(session, teacher_id: str) -> ActivityAdaptation:
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        title="Teste Áudio",
        statement="A horta tem alface.",
        question="O que tem na horta?",
        status="active",
    )
    session.add(activity)
    session.flush()

    output = _mock_adaptation(
        {"title": activity.title, "statement": activity.statement, "question": activity.question},
        {"name": "TEA — Não Verbal"},
    )
    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        generated_by="mock",
        output_data=output,
        status="review",
        version=1,
    )
    session.add(adaptation)

    api_key = ApiKey(
        id=str(uuid.uuid4()),
        user_id=teacher_id,
        provider="openai",
        key_name="test-key",
        encrypted_value="sk-fake-key",
        status="active",
    )
    session.add(api_key)
    session.commit()
    session.refresh(adaptation)
    return adaptation


def test_generate_audio_requires_api_key(client, session):
    teacher = create_user(session, role="teacher", suffix="_audio_nokey")
    token = get_token(client, teacher.email)

    # No API key for this teacher — create adaptation directly
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        title="Sem Key",
        status="active",
    )
    session.add(activity)
    session.flush()
    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        generated_by="mock",
        output_data={"audio_options": [{"id": "audio_1", "script": "texto", "tts_script": "texto"}]},
        status="review",
        version=1,
    )
    session.add(adaptation)
    session.commit()

    resp = client.post(
        f"/adaptations/{adaptation.id}/generate-audio",
        headers=auth(token),
    )
    assert resp.status_code == 400
    assert "OpenAI" in resp.json()["detail"]


def test_generate_audio_endpoint_updates_audio_url(client, session, monkeypatch):
    fake_url = "http://test/static/audio/fake.mp3"

    async def fake_tts(*args, **kwargs):
        return fake_url

    monkeypatch.setattr("app.routes.adaptations.generate_audio_tts", fake_tts)

    teacher = create_user(session, role="teacher", suffix="_audio_key1")
    token = get_token(client, teacher.email)
    adaptation = _seed_adaptation_with_audio_key(session, teacher.id)

    resp = client.post(
        f"/adaptations/{adaptation.id}/generate-audio",
        headers=auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated"] >= 1
    assert any(opt.get("audio_url") == fake_url for opt in data["audio_options"])


def test_generate_audio_skips_already_generated(client, session, monkeypatch):
    call_count = {"n": 0}

    async def counting_tts(*args, **kwargs):
        call_count["n"] += 1
        return "http://test/static/audio/already.mp3"

    monkeypatch.setattr("app.routes.adaptations.generate_audio_tts", counting_tts)

    teacher = create_user(session, role="teacher", suffix="_audio_skip")
    token = get_token(client, teacher.email)
    adaptation = _seed_adaptation_with_audio_key(session, teacher.id)

    # First call generates
    client.post(f"/adaptations/{adaptation.id}/generate-audio", headers=auth(token))
    first_count = call_count["n"]
    assert first_count >= 1

    # Second call without force should skip (audio_url already set)
    client.post(f"/adaptations/{adaptation.id}/generate-audio", headers=auth(token))
    assert call_count["n"] == first_count


def test_generate_audio_force_regenerates(client, session, monkeypatch):
    call_count = {"n": 0}

    async def counting_tts(*args, **kwargs):
        call_count["n"] += 1
        return f"http://test/static/audio/{call_count['n']}.mp3"

    monkeypatch.setattr("app.routes.adaptations.generate_audio_tts", counting_tts)

    teacher = create_user(session, role="teacher", suffix="_audio_force")
    token = get_token(client, teacher.email)
    adaptation = _seed_adaptation_with_audio_key(session, teacher.id)

    client.post(f"/adaptations/{adaptation.id}/generate-audio", headers=auth(token))
    first_count = call_count["n"]

    # force=true should regenerate even when audio_url is set
    client.post(
        f"/adaptations/{adaptation.id}/generate-audio?force=true",
        headers=auth(token),
    )
    assert call_count["n"] > first_count


# ─── E2E (real OpenAI TTS — requires OPENAI_TEST_API_KEY) ────────────────────

def test_e2e_generate_real_audio_file(tmp_path, monkeypatch):
    api_key = os.environ.get("OPENAI_TEST_API_KEY")
    if not api_key:
        pytest.skip("Set OPENAI_TEST_API_KEY to run E2E TTS test")

    monkeypatch.setattr("app.services.openai_service._AUDIO_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.openai_service._API_BASE_URL", "http://test")

    url = asyncio.run(generate_audio_tts(api_key, "Horta tem alface.", "alloy", 1.0))
    assert url.startswith("http://test/static/audio/")
    filename = url.split("/")[-1]
    path = tmp_path / filename
    assert path.exists(), f"MP3 file not created at {path}"
    assert path.stat().st_size > 1000, "MP3 file should be non-trivial in size"
