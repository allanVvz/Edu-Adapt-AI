"""
CI/CD tests for DALL-E image generation.
All OpenAI calls are mocked — no real API keys required.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.activity import Activity
from app.models.adaptation import ActivityAdaptation
from app.models.api_key import ApiKey
from app.services.openai_service import _mock_adaptation, IMAGE_STYLES, VALID_IMAGE_MODELS
from .conftest import create_user, get_token, auth

FAKE_URL = "https://mock-dalle.com/test-image.png"


def _seed_adaptation_with_key(session, teacher_id: str) -> ActivityAdaptation:
    """Create adaptation + OpenAI API key for teacher."""
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        title="Rotina da Manhã",
        statement="Observe as imagens.",
        question="Qual é a ordem correta?",
        expected_answer="acordar, escovar os dentes, tomar café",
        activity_type="sequencing",
        status="active",
    )
    session.add(activity)
    session.flush()

    output = _mock_adaptation(
        {"title": activity.title, "statement": activity.statement,
         "question": activity.question, "expected_answer": activity.expected_answer,
         "activity_type": activity.activity_type},
        {},
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
        key_name="test-openai-key",
        encrypted_value="sk-fake-key-for-tests",
        status="active",
    )
    session.add(api_key)
    session.commit()
    session.refresh(adaptation)
    return adaptation


@pytest.fixture
def mock_dalle():
    """Fixture that mocks AsyncOpenAI to return a fake image URL."""
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(url=FAKE_URL)]
    with patch("openai.AsyncOpenAI") as mock_cls:
        instance = MagicMock()
        instance.images.generate = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = instance
        yield mock_cls


def test_image_styles_use_valid_models():
    """
    CONTRACT TEST — no mock, no network.
    Fails immediately if IMAGE_STYLES references a deprecated or non-existent model.
    This is the guard that would have caught the dall-e-2 deprecation before deploy.
    """
    VALID_SIZES = {
        "1024x1024", "1024x1792", "1792x1024",  # dall-e-3
        "1536x1024", "1024x1536", "auto",         # gpt-image-1
    }
    for style_name, cfg in IMAGE_STYLES.items():
        assert "model" in cfg, f"Style '{style_name}' is missing the 'model' field"
        assert cfg["model"] in VALID_IMAGE_MODELS, (
            f"Style '{style_name}' uses model '{cfg['model']}' which is not in VALID_IMAGE_MODELS "
            f"{sorted(VALID_IMAGE_MODELS)}. Update IMAGE_STYLES in openai_service.py."
        )
        assert cfg["size"] in VALID_SIZES, (
            f"Style '{style_name}' uses size '{cfg['size']}' which is not valid for model '{cfg['model']}'. "
            f"Valid sizes: {sorted(VALID_SIZES)}"
        )


def test_mock_adaptation_has_new_schema():
    """_mock_adaptation should produce image_options with prompts for all styles."""
    output = _mock_adaptation({"title": "Test", "expected_answer": "A, B, C"}, {})

    assert "image_options" in output
    for img in output["image_options"]:
        assert "prompts" in img, "image_option missing 'prompts'"
        for style in IMAGE_STYLES:
            assert style in img["prompts"], f"missing style '{style}' in prompts"
        assert "generated" in img
        assert "active_style" in img
        assert "is_active" in img
        assert "image_url" in img

    interaction = output["interaction_options"][0]
    for item in interaction["items"]:
        assert "prompts" in item, "item missing 'prompts'"
        for style in IMAGE_STYLES:
            assert style in item["prompts"]
        assert "active_style" in item


def test_generate_images_cartoon_2d_stores_url(client, session, mock_dalle):
    """Generating cartoon_2d should store the URL in generated.cartoon_2d.image_url."""
    teacher = create_user(session, role="teacher", suffix="_img1")
    adaptation = _seed_adaptation_with_key(session, teacher.id)
    token = get_token(client, teacher.email)

    r = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["images_generated"] > 0
    assert body["errors"] == []

    # Reload and verify storage
    session.expire_all()
    updated = session.get(ActivityAdaptation, adaptation.id)
    img = updated.output_data["image_options"][0]
    assert img["generated"]["cartoon_2d"]["image_url"] == FAKE_URL


def test_generate_images_line_art_stores_url(client, session, mock_dalle):
    """Generating line_art should store URL in generated.line_art.image_url."""
    teacher = create_user(session, role="teacher", suffix="_img2")
    adaptation = _seed_adaptation_with_key(session, teacher.id)
    token = get_token(client, teacher.email)

    r = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "line_art"},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert r.json()["images_generated"] > 0

    session.expire_all()
    updated = session.get(ActivityAdaptation, adaptation.id)
    img = updated.output_data["image_options"][0]
    assert img["generated"]["line_art"]["image_url"] == FAKE_URL


def test_generate_images_skips_already_generated(client, session, mock_dalle):
    """If a style already has image_url, it should be skipped (images_generated == 0)."""
    teacher = create_user(session, role="teacher", suffix="_img3")
    adaptation = _seed_adaptation_with_key(session, teacher.id)
    token = get_token(client, teacher.email)

    # First generation
    client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )

    # Second attempt — should skip all already-generated
    r = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert r.json()["images_generated"] == 0


def test_generate_images_reports_errors(client, session):
    """When DALL-E raises an exception, errors should be reported (not silently swallowed)."""
    teacher = create_user(session, role="teacher", suffix="_img4")
    adaptation = _seed_adaptation_with_key(session, teacher.id)
    token = get_token(client, teacher.email)

    with patch("openai.AsyncOpenAI") as mock_cls:
        instance = MagicMock()
        instance.images.generate = AsyncMock(side_effect=Exception("API rate limit"))
        mock_cls.return_value = instance

        r = client.post(
            f"/adaptations/{adaptation.id}/generate-images",
            json={"style": "cartoon_2d"},
            headers=auth(token),
        )

    assert r.status_code == 200
    body = r.json()
    assert body["images_generated"] == 0
    assert len(body["errors"]) > 0
    assert "API rate limit" in body["errors"][0]["error"]


def test_set_image_style_updates_image_url(client, session, mock_dalle):
    """set-image-style should copy generated[style].image_url to top-level image_url."""
    teacher = create_user(session, role="teacher", suffix="_img5")
    adaptation = _seed_adaptation_with_key(session, teacher.id)
    token = get_token(client, teacher.email)

    # Generate line_art first
    client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "line_art"},
        headers=auth(token),
    )

    session.expire_all()
    updated = session.get(ActivityAdaptation, adaptation.id)
    img_id = updated.output_data["image_options"][0]["id"]

    # Apply line_art style
    r = client.post(
        f"/adaptations/{adaptation.id}/image-style",
        json={"style": "line_art", "active_image_ids": [img_id]},
        headers=auth(token),
    )
    assert r.status_code == 200

    session.expire_all()
    final = session.get(ActivityAdaptation, adaptation.id)
    img = final.output_data["image_options"][0]
    assert img["active_style"] == "line_art"
    assert img["is_active"] is True
    assert img["image_url"] == FAKE_URL


def test_generate_images_requires_api_key(client, session):
    """Teacher without OpenAI key should get HTTP 400."""
    teacher = create_user(session, role="teacher", suffix="_img6")
    # No ApiKey created for this teacher
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        title="Test",
        statement="Test",
        question="Test?",
        expected_answer="A",
        activity_type="test",
        status="active",
    )
    session.add(activity)
    session.flush()
    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        generated_by="mock",
        output_data=_mock_adaptation({"title": "Test", "expected_answer": "A"}, {}),
        status="review",
        version=1,
    )
    session.add(adaptation)
    session.commit()

    token = get_token(client, teacher.email)
    r = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )
    assert r.status_code == 400
    assert "Chave OpenAI" in r.json()["detail"]
