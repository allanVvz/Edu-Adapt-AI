"""
CI/CD tests for image generation.

Unit/integration tests: all OpenAI calls are mocked — no real API keys required.
E2E test: requires OPENAI_TEST_API_KEY env var — calls the real OpenAI API.
"""
import os
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.activity import Activity
from app.models.adaptation import ActivityAdaptation
from app.models.api_key import ApiKey
from app.services.openai_service import (
    _mock_adaptation, _get_profile_image_modifier, IMAGE_STYLES, VALID_IMAGE_MODELS,
)
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
    History: dall-e-2 was deprecated Nov 2024; dall-e-3 was removed 2025; gpt-image-1 is current.
    """
    VALID_SIZES = {
        "1024x1024", "1024x1792", "1792x1024",  # dall-e-3 (legacy)
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


# ─── Profile image modifier tests ────────────────────────────────────────────

def test_profile_modifier_nao_verbal_returns_aac_style():
    """TEA — Não Verbal profile should produce AAC pictogram modifier."""
    modifier = _get_profile_image_modifier("TEA — Não Verbal")
    assert modifier != "", "Non-verbal profile should have a modifier"
    low_mod = modifier.lower()
    assert "aac" in low_mod or "pictogram" in low_mod, (
        f"Non-verbal modifier should reference AAC pictogram style, got: {modifier}"
    )
    # Must avoid rich imagery keywords
    assert "vibrant" not in low_mod
    assert "colorful" not in low_mod


def test_profile_modifier_hipersensibilidade_returns_muted():
    """TEA — Hipersensibilidade Visual should produce desaturated/muted modifier."""
    modifier = _get_profile_image_modifier("TEA — Hipersensibilidade Visual")
    assert modifier != "", "Hipersensibilidade profile should have a modifier"
    low_mod = modifier.lower()
    # Must contain desaturation/muted cues
    assert any(kw in low_mod for kw in ("desaturated", "muted", "pastel", "soft")), (
        f"Hipersensibilidade modifier should contain muted/desaturated cues, got: {modifier}"
    )
    # Must NOT promote vibrant colors
    assert "vibrant" not in low_mod
    assert "bright" not in low_mod


def test_profile_modifier_apoio_visual_returns_colorful():
    """TEA — Apoio Visual e Leitura Inicial should produce colorful/friendly modifier."""
    modifier = _get_profile_image_modifier("TEA — Apoio Visual e Leitura Inicial")
    assert modifier != "", "Apoio Visual profile should have a modifier"
    low_mod = modifier.lower()
    assert any(kw in low_mod for kw in ("colorful", "bright", "cartoon", "friendly")), (
        f"Apoio Visual modifier should contain colorful/friendly cues, got: {modifier}"
    )


def test_profile_modifier_hipersensibilidade_is_less_colorful_than_apoio_visual():
    """
    Validates the business rule: Hipersensibilidade images must be less colorful than Apoio Visual.
    Proxy: Hipersensibilidade modifier must NOT contain colorfulness keywords that Apoio Visual has.
    """
    mod_hip = _get_profile_image_modifier("TEA — Hipersensibilidade Visual").lower()
    mod_apo = _get_profile_image_modifier("TEA — Apoio Visual e Leitura Inicial").lower()

    colorful_kws = {"colorful", "bright", "vibrant", "rich color"}
    muted_kws = {"desaturated", "muted", "pastel", "soft", "low visual noise"}

    hip_has_colorful = any(kw in mod_hip for kw in colorful_kws)
    apo_has_colorful = any(kw in mod_apo for kw in colorful_kws)
    hip_has_muted = any(kw in mod_hip for kw in muted_kws)

    assert not hip_has_colorful, (
        f"Hipersensibilidade should NOT have colorfulness keywords. Got: {mod_hip}"
    )
    assert apo_has_colorful or ("cartoon" in mod_apo), (
        f"Apoio Visual should have colorfulness/cartoon keywords. Got: {mod_apo}"
    )
    assert hip_has_muted, (
        f"Hipersensibilidade should have muted/desaturated keywords. Got: {mod_hip}"
    )


def test_profile_modifier_unknown_profile_returns_empty():
    """Unknown profiles should return empty string (no modifier = standard generation)."""
    modifier = _get_profile_image_modifier("Perfil Desconhecido")
    assert modifier == "", f"Unknown profile should return empty modifier, got: {modifier!r}"


def test_profile_modifier_stored_as_prompt_used_in_output(client, session, mock_dalle):
    """When a profile has a modifier, generated[style].prompt_used should contain the modifier."""
    from app.models.student_profile import StudentProfile

    teacher = create_user(session, role="teacher", suffix="_mod1")

    # Create TEA — Hipersensibilidade Visual profile
    profile = StudentProfile(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        name="TEA — Hipersensibilidade Visual",
        reading_level="basic",
        autonomy_level="medium",
    )
    session.add(profile)
    session.flush()

    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        title="Cores e Formas",
        statement="Observe.",
        question="Qual é a cor?",
        expected_answer="Vermelho, Azul",
        activity_type="association",
        status="active",
    )
    session.add(activity)
    session.flush()

    output = _mock_adaptation(
        {"title": activity.title, "statement": activity.statement,
         "question": activity.question, "expected_answer": activity.expected_answer,
         "activity_type": activity.activity_type},
        {"name": profile.name},
    )
    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        student_profile_id=profile.id,
        generated_by="mock",
        output_data=output,
        status="review",
        version=1,
    )
    session.add(adaptation)

    from app.models.api_key import ApiKey
    api_key = ApiKey(
        id=str(uuid.uuid4()),
        user_id=teacher.id,
        provider="openai",
        key_name="test-key-modifier",
        encrypted_value="sk-fake-key",
        status="active",
    )
    session.add(api_key)
    session.commit()

    token = get_token(client, teacher.email)
    r = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )
    assert r.status_code == 200

    session.expire_all()
    updated = session.get(ActivityAdaptation, adaptation.id)
    img = updated.output_data["image_options"][0]
    prompt_used = img["generated"]["cartoon_2d"].get("prompt_used", "")

    # The modifier should be in the prompt_used
    expected_modifier_kw = "desaturated"  # from Hipersensibilidade modifier
    assert expected_modifier_kw in prompt_used.lower(), (
        f"prompt_used should contain the profile modifier keyword '{expected_modifier_kw}'. "
        f"Got: {prompt_used[:200]}"
    )


# ─── E2E test (requires real API key) ────────────────────────────────────────

_REAL_KEY = os.environ.get("OPENAI_TEST_API_KEY", "")


@pytest.mark.skipif(not _REAL_KEY, reason="E2E: set OPENAI_TEST_API_KEY to run against the real OpenAI API")
def test_e2e_generate_4_images_real_api(client, session):
    """
    E2E TEST — calls the real OpenAI gpt-image-1 API.
    Activity: Rotina da Manhã (2 image_options + 2 interaction items = 4 slots).
    Validates that all 4 images are generated and have valid HTTPS URLs.
    """
    teacher = create_user(session, role="teacher", suffix="_e2e")

    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher.id,
        title="Rotina da Manhã",
        statement="Observe as imagens e coloque na ordem correta.",
        question="Qual é a sequência correta da manhã?",
        expected_answer="acordar, escovar os dentes",
        activity_type="sequencing",
        status="active",
    )
    session.add(activity)
    session.flush()

    output = _mock_adaptation(
        {
            "title": activity.title,
            "statement": activity.statement,
            "question": activity.question,
            "expected_answer": activity.expected_answer,
            "activity_type": activity.activity_type,
        },
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

    api_key_obj = ApiKey(
        id=str(uuid.uuid4()),
        user_id=teacher.id,
        provider="openai",
        key_name="e2e-real-key",
        encrypted_value=_REAL_KEY,
        status="active",
    )
    session.add(api_key_obj)
    session.commit()
    session.refresh(adaptation)

    token = get_token(client, teacher.email)
    r = client.post(
        f"/adaptations/{adaptation.id}/generate-images",
        json={"style": "cartoon_2d"},
        headers=auth(token),
    )

    assert r.status_code == 200, f"generate-images failed: {r.text}"
    body = r.json()
    assert body["errors"] == [], f"Generation errors: {body['errors']}"
    assert body["images_generated"] == 4, (
        f"Expected 4 images (2 image_options + 2 items), got {body['images_generated']}"
    )

    session.expire_all()
    updated = session.get(ActivityAdaptation, adaptation.id)

    all_urls = []
    for img in updated.output_data["image_options"]:
        url = img["generated"]["cartoon_2d"]["image_url"]
        assert url and url.startswith("https://"), f"image_option '{img['id']}' has no valid URL: {url}"
        all_urls.append(url)

    for interaction in updated.output_data["interaction_options"]:
        for item in interaction["items"]:
            url = item["generated"]["cartoon_2d"]["image_url"]
            assert url and url.startswith("https://"), f"item '{item['name']}' has no valid URL: {url}"
            all_urls.append(url)

    assert len(all_urls) == 4, f"Expected 4 URLs total, got {len(all_urls)}"
