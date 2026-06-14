"""
Tests for agent output structure and cyclomatic integrity.
Uses _mock_adaptation as a deterministic baseline — the same
structure is expected from the real OpenAI path.
"""
import pytest
from app.services.openai_service import _mock_adaptation

ACTIVITY = {
    "title": "Animais e Ambientes",
    "statement": "Observe os animais e associe ao ambiente.",
    "question": "Onde cada animal vive?",
    "expected_answer": "Peixe vive na água. Cachorro vive na terra. Pássaro vive no ar.",
    "activity_type": "drag_drop",
}

PROFILE = {
    "name": "Apoio visual",
    "main_difficulties": ["textos longos"],
    "recommended_strategies": ["imagens", "frases curtas"],
    "preferred_modalities": ["visual", "audio"],
}


@pytest.fixture()
def output():
    return _mock_adaptation(ACTIVITY, PROFILE)


def test_output_has_all_required_keys(output):
    required = {"text_adaptations", "image_options", "audio_options", "interaction_options", "validation"}
    assert required.issubset(output.keys()), f"Missing keys: {required - output.keys()}"


def test_text_adaptations_structure(output):
    items = output["text_adaptations"]
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert "version" in item
        assert "content" in item
        assert isinstance(item["version"], int)
        assert isinstance(item["content"], str)
        assert len(item["content"]) > 0


def test_image_options_structure(output):
    items = output["image_options"]
    assert isinstance(items, list)
    assert len(items) >= 1
    for img in items:
        assert "id" in img
        assert "description" in img
        assert "prompts" in img
        assert isinstance(img["prompts"], dict)
        assert "line_art" in img["prompts"]
        assert "cartoon_2d" in img["prompts"]


def test_audio_options_structure(output):
    items = output["audio_options"]
    assert isinstance(items, list)
    assert len(items) >= 1
    for audio in items:
        assert "id" in audio
        assert "script" in audio
        assert "voice_style" in audio


def test_interaction_items_are_dicts(output):
    """Items in interaction_options are dicts with name + prompts (image-ready schema)."""
    for interaction in output["interaction_options"]:
        for item in interaction.get("items", []):
            assert isinstance(item, dict), (
                f"interaction item must be dict, got {type(item).__name__}: {item!r}"
            )
            assert "name" in item, f"item missing 'name': {item!r}"
            assert "prompts" in item, f"item missing 'prompts': {item!r}"
            assert isinstance(item["prompts"], dict)


def test_interaction_zones_are_dicts(output):
    """Zones are dicts with a 'name' key (label for the drop target)."""
    for interaction in output["interaction_options"]:
        for zone in interaction.get("zones", []):
            assert isinstance(zone, dict), (
                f"zone must be dict, got {type(zone).__name__}: {zone!r}"
            )
            assert "name" in zone, f"zone missing 'name': {zone!r}"


def test_validation_scores_in_range(output):
    v = output["validation"]
    for field in ("clarity_score", "accessibility_score", "pedagogical_score"):
        assert field in v
        assert 1 <= v[field] <= 5, f"{field} out of range: {v[field]}"


def test_validation_approved_is_bool(output):
    assert isinstance(output["validation"]["approved"], bool)


def test_empty_profile_doesnt_crash():
    result = _mock_adaptation(ACTIVITY, {})
    assert "text_adaptations" in result


def test_empty_activity_doesnt_crash():
    result = _mock_adaptation({}, PROFILE)
    assert "text_adaptations" in result
