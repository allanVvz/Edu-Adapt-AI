"""
Tests for emoji-as-illustration feature.

Validates concept → emoji lookup and that generate-images respects
illustration_type == "emoji" (skip unless force=true).
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.emoji_service import get_emoji_for_concept, CONCEPT_EMOJI
from app.services.openai_service import _mock_adaptation, _build_image_option
from app.models.activity import Activity
from app.models.adaptation import ActivityAdaptation
from app.models.api_key import ApiKey
from .conftest import create_user, get_token, auth

# ─── Lookup tests ─────────────────────────────────────────────────────────────

def test_known_concept_alface_returns_emoji():
    assert get_emoji_for_concept("alface") == "🥬"


def test_known_concept_tomate_returns_emoji():
    assert get_emoji_for_concept("tomate") == "🍅"


def test_unknown_concept_returns_none():
    assert get_emoji_for_concept("xyzabc123zyx") is None


def test_empty_string_returns_none():
    assert get_emoji_for_concept("") is None


def test_whitespace_only_returns_none():
    assert get_emoji_for_concept("   ") is None


def test_case_insensitive_uppercase():
    assert get_emoji_for_concept("ALFACE") == "🥬"


def test_case_insensitive_mixed():
    assert get_emoji_for_concept("Alface") == "🥬"


def test_partial_match_in_longer_text():
    result = get_emoji_for_concept("horta de alface e tomate")
    assert result is not None


def test_guarda_chuva_beats_chuva():
    """Longest match wins: 'guarda-chuva' should return umbrella, not rain."""
    result = get_emoji_for_concept("guarda-chuva")
    assert result == "☂️"


def test_all_concept_values_are_non_empty_strings():
    for key, emoji in CONCEPT_EMOJI.items():
        assert isinstance(emoji, str) and len(emoji) >= 1, f"Bad emoji for '{key}'"


def test_multiple_disciplines_covered():
    """At least one concept from each of the 5 disciplines resolves."""
    assert get_emoji_for_concept("alface") is not None       # Português AT-PORT-01
    assert get_emoji_for_concept("triângulo") is not None    # Matemática AT-MAT-03
    assert get_emoji_for_concept("sapo") is not None         # Ciências AT-CIE-03
    assert get_emoji_for_concept("bebê") is not None         # História AT-HIS-01
    assert get_emoji_for_concept("avião") is not None        # Geografia AT-GEO-05


# ─── _build_image_option tests ────────────────────────────────────────────────

def test_image_option_with_known_concept_has_emoji_type():
    opt = _build_image_option("img_1", "Ilustração de alface", "alface illustration")
    assert opt["illustration_type"] == "emoji"
    assert "emoji" in opt
    assert opt["emoji"] == "🥬"


def test_image_option_with_unknown_concept_has_generated_type():
    opt = _build_image_option("img_1", "abstract unknown xyz", "xyz")
    assert opt["illustration_type"] == "generated"
    assert "emoji" not in opt


def test_image_option_always_has_prompts():
    opt = _build_image_option("img_1", "alface", "alface, educational")
    assert "prompts" in opt
    assert "line_art" in opt["prompts"]
    assert "cartoon_2d" in opt["prompts"]


def test_image_option_always_has_generated_slots():
    opt = _build_image_option("img_1", "alface", "alface")
    assert "generated" in opt
    assert "line_art" in opt["generated"]
    assert "cartoon_2d" in opt["generated"]


# ─── _mock_adaptation emoji integration ───────────────────────────────────────

def test_mock_adaptation_image_options_have_illustration_type():
    activity = {
        "title": "Horta da escola",
        "statement": "A horta tem alface.",
        "question": "O que tem na horta?",
    }
    result = _mock_adaptation(activity, {})
    for img in result["image_options"]:
        assert "illustration_type" in img, f"Missing illustration_type in {img['id']}"


# ─── generate-images skips emoji slots ────────────────────────────────────────

@pytest.fixture
def mock_dalle():
    fake_resp = MagicMock()
    fake_resp.data = [MagicMock(url="https://mock.openai/image.png", b64_json=None)]
    with patch("openai.AsyncOpenAI") as mock_cls:
        instance = MagicMock()
        instance.images.generate = AsyncMock(return_value=fake_resp)
        mock_cls.return_value = instance
        yield mock_cls


def _seed_adaptation_with_emoji_options(session, teacher_id: str) -> ActivityAdaptation:
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        title="Emoji Test Activity",
        statement="Emoji test.",
        status="active",
    )
    session.add(activity)
    session.flush()

    output = {
        "image_options": [
            {
                "id": "img_1",
                "description": "Ilustração de alface",
                "base_subject": "alface illustration",
                "prompts": {"line_art": "alface, line art", "cartoon_2d": "alface, cartoon"},
                "generated": {"line_art": {"image_url": None, "generated_at": None},
                              "cartoon_2d": {"image_url": None, "generated_at": None}},
                "active_style": "cartoon_2d",
                "is_active": True,
                "image_url": None,
                "illustration_type": "emoji",
                "emoji": "🥬",
            },
            {
                "id": "img_2",
                "description": "Conceito desconhecido abstrato",
                "base_subject": "unknown abstract concept",
                "prompts": {"line_art": "unknown, line art", "cartoon_2d": "unknown, cartoon"},
                "generated": {"line_art": {"image_url": None, "generated_at": None},
                              "cartoon_2d": {"image_url": None, "generated_at": None}},
                "active_style": "cartoon_2d",
                "is_active": True,
                "image_url": None,
                "illustration_type": "generated",
            },
        ],
        "audio_options": [],
        "interaction_options": [],
        "text_adaptations": [{"version": 1, "content": "texto"}],
        "validation": {"approved": True, "clarity_score": 4, "accessibility_score": 4,
                       "pedagogical_score": 4, "difficulty_score": 3},
    }

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
        encrypted_value="sk-fake",
        status="active",
    )
    session.add(api_key)
    session.commit()
    session.refresh(adaptation)
    return adaptation


def test_generate_images_skips_emoji_slot(client, session, mock_dalle):
    teacher = create_user(session, role="teacher", suffix="_emoji_skip")
    token = get_token(client, teacher.email)
    adaptation = _seed_adaptation_with_emoji_options(session, teacher.id)

    resp = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )
    assert resp.status_code == 200

    # The OpenAI images.generate should have been called exactly once (only img_2)
    instance = mock_dalle.return_value
    assert instance.images.generate.call_count == 1


def test_generate_images_force_generates_emoji_slot(client, session, mock_dalle):
    teacher = create_user(session, role="teacher", suffix="_emoji_force")
    token = get_token(client, teacher.email)
    adaptation = _seed_adaptation_with_emoji_options(session, teacher.id)

    resp = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d", "force": True},
        headers=auth(token),
    )
    assert resp.status_code == 200

    # With force=true, both images should be generated
    instance = mock_dalle.return_value
    assert instance.images.generate.call_count == 2
