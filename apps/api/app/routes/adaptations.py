from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.adaptation import ActivityAdaptation
from ..models.activity import Activity
from ..models.story import Story
from ..models.student import Student
from ..models.student_profile import StudentProfile
from ..models.user import User
from ..routes.auth import require_role
from ..services.openai_service import get_user_openai_key, generate_adaptation_with_ai, _mock_adaptation, IMAGE_STYLES, VALID_IMAGE_MODELS, _parse_image_error, _save_image, _get_profile_image_modifier, generate_audio_tts, make_openai_client
from ..services.static_url_service import normalized_output_data
from ..services.educational_validation_service import apply_educational_quality_gate, educational_blockers
from ..services.pdf_service import AdaptationPDFRenderer
from ..services.pdf_constants import get_profile_config
from ..models.gallery_image import GalleryImage
from ..services.icon_symbol_service import apply_icon_symbol, find_icon_symbol, normalize_term
import uuid

router = APIRouter(prefix="/adaptations", tags=["adaptations"])


class FeedbackRequest(BaseModel):
    feedback: Optional[str] = None


def _story_pdf_data(story: Story | None) -> dict | None:
    if not story:
        return None
    return {
        "id": story.id,
        "title": story.title,
        "content": story.content,
        "image_options": story.image_options or [],
        "audio_options": story.audio_options or [],
    }


def _activity_math_context(activity: Activity | None) -> dict:
    if not activity:
        return {}
    return {
        "title": activity.title,
        "discipline": activity.discipline,
        "statement": activity.statement,
        "question": activity.question,
        "expected_answer": activity.expected_answer,
        "teacher_notes": activity.teacher_notes,
    }


@router.get("")
def list_adaptations(
    status: Optional[str] = None,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    query = select(ActivityAdaptation).order_by(ActivityAdaptation.created_at.desc())
    if status:
        query = query.where(ActivityAdaptation.status == status)
    adaptations = session.exec(query.limit(100)).all()
    result = []
    for a in adaptations:
        activity = session.get(Activity, a.activity_id)
        profile = session.get(StudentProfile, a.student_profile_id) if a.student_profile_id else None
        student_name = None
        if a.student_id:
            student = session.get(Student, a.student_id)
            if student:
                su = session.get(User, student.user_id)
                student_name = su.name if su else None
        result.append({
            "id": a.id,
            "activity": {"id": activity.id, "title": activity.title} if activity else None,
            "profile": {"id": profile.id, "name": profile.name} if profile else None,
            "student_id": a.student_id,
            "student_name": student_name,
            "generated_by": a.generated_by,
            "status": a.status,
            "version": a.version,
            "created_at": str(a.created_at),
        })
    return result


@router.get("/{adaptation_id}")
def get_adaptation(
    adaptation_id: str,
    request: Request,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    activity = session.get(Activity, adaptation.activity_id)
    profile = session.get(StudentProfile, adaptation.student_profile_id) if adaptation.student_profile_id else None

    teacher = None
    if activity:
        teacher = session.get(User, activity.teacher_id)

    student_name = None
    if adaptation.student_id:
        student = session.get(Student, adaptation.student_id)
        if student:
            su = session.get(User, student.user_id)
            student_name = su.name if su else None

    return {
        "id": adaptation.id,
        "activity": {
            "id": activity.id,
            "title": activity.title,
            "teacher_id": activity.teacher_id,
            "teacher_name": teacher.name if teacher else None,
        } if activity else None,
        "profile": {"id": profile.id, "name": profile.name} if profile else None,
        "student_id": adaptation.student_id,
        "student_name": student_name,
        "generated_by": adaptation.generated_by,
        "status": adaptation.status,
        "version": adaptation.version,
        "output": normalized_output_data(
            adaptation.output_data,
            str(request.base_url).rstrip("/"),
            activity=_activity_math_context(activity),
        ),
        "validator_feedback": adaptation.validator_feedback,
        "teacher_feedback": adaptation.teacher_feedback,
        "created_at": adaptation.created_at,
    }


@router.post("/{adaptation_id}/approve")
def approve_adaptation(
    adaptation_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")
    adaptation.status = "approved"
    adaptation.updated_at = datetime.utcnow()
    session.add(adaptation)
    session.commit()
    return {"status": "approved"}


@router.post("/{adaptation_id}/reject")
def reject_adaptation(
    adaptation_id: str,
    body: FeedbackRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")
    adaptation.status = "rejected"
    adaptation.teacher_feedback = body.feedback
    adaptation.updated_at = datetime.utcnow()
    session.add(adaptation)
    session.commit()
    return {"status": "rejected"}


@router.post("/{adaptation_id}/publish")
def publish_adaptation(
    adaptation_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")
    if adaptation.status not in ("approved", "review", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot publish adaptation in current status")
    activity = session.get(Activity, adaptation.activity_id)
    checked_output = apply_educational_quality_gate(adaptation.output_data or {}, _activity_math_context(activity))
    blockers = educational_blockers(checked_output)
    if blockers:
        adaptation.output_data = checked_output
        adaptation.status = "review"
        adaptation.validator_feedback = "; ".join(blocker.get("message", "Erro educacional") for blocker in blockers)
        session.add(adaptation)
        session.commit()
        raise HTTPException(status_code=422, detail={"message": "Educational validation failed", "blockers": blockers})
    adaptation.output_data = checked_output
    adaptation.status = "published"
    adaptation.updated_at = datetime.utcnow()
    session.add(adaptation)
    session.commit()
    return {"status": "published"}


@router.post("/{adaptation_id}/reprocess")
async def reprocess_adaptation(
    adaptation_id: str,
    body: FeedbackRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    activity = session.get(Activity, adaptation.activity_id)
    profile = session.get(StudentProfile, adaptation.student_profile_id) if adaptation.student_profile_id else None

    activity_dict = {
        "title": activity.title if activity else "",
        "statement": activity.statement if activity else "",
        "question": activity.question if activity else "",
        "expected_answer": activity.expected_answer if activity else "",
        "discipline": activity.discipline if activity else "",
        "pedagogical_objective": activity.pedagogical_objective if activity else "",
        "activity_type": activity.activity_type if activity else "",
    }
    profile_dict = {}
    if profile:
        profile_dict = {
            "name": profile.name,
            "main_difficulties": profile.main_difficulties,
            "recommended_strategies": profile.recommended_strategies,
            "preferred_modalities": profile.preferred_modalities,
        }

    openai_key = get_user_openai_key(session, current_user.id)
    if openai_key:
        output = await generate_adaptation_with_ai(openai_key, activity_dict, profile_dict)
        generated_by = "openai"
    else:
        output = _mock_adaptation(activity_dict, profile_dict)
        generated_by = "mock"
    output = apply_educational_quality_gate(output, activity_dict)

    new_adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=adaptation.activity_id,
        student_profile_id=adaptation.student_profile_id,
        student_id=adaptation.student_id,
        generated_by=generated_by,
        output_data=output,
        status="review",
        teacher_feedback=body.feedback,
        version=adaptation.version + 1,
    )
    session.add(new_adaptation)
    session.commit()
    session.refresh(new_adaptation)
    return {"id": new_adaptation.id, "version": new_adaptation.version, "status": new_adaptation.status}


DEFAULT_IMAGE_STYLE = "pictogram"


class GenerateImagesRequest(BaseModel):
    style: str = DEFAULT_IMAGE_STYLE
    force: bool = False


class SetImageStyleRequest(BaseModel):
    style: str
    active_image_ids: list[str] = []


@router.post("/{adaptation_id}/generate-images")
async def generate_images(
    adaptation_id: str,
    body: GenerateImagesRequest = GenerateImagesRequest(),
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if body.style not in IMAGE_STYLES:
        raise HTTPException(status_code=400, detail=f"Estilo inválido. Opções: {list(IMAGE_STYLES.keys())}")

    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    openai_key = get_user_openai_key(session, current_user.id)
    if body.style != "pictogram" and not openai_key:
        raise HTTPException(status_code=400, detail="Chave OpenAI não configurada. Acesse Configurações → Chaves de API.")

    import copy
    from datetime import datetime

    client = make_openai_client(openai_key) if body.style != "pictogram" and openai_key else None
    style = body.style
    style_cfg = IMAGE_STYLES[style]
    model = style_cfg["model"]
    size = style_cfg["size"]

    # Guard: reject if model is not in the known-valid list
    if body.style != "pictogram" and model not in VALID_IMAGE_MODELS:
        raise HTTPException(
            status_code=500,
            detail=f"Modelo de imagem '{model}' não é suportado. Modelos válidos: {sorted(VALID_IMAGE_MODELS)}"
        )

    output = copy.deepcopy(adaptation.output_data or {})
    generated_count = 0
    errors = []

    # Profile image modifier — appended to prompts at generation time
    profile_modifier = ""
    if adaptation.student_profile_id:
        profile = session.get(StudentProfile, adaptation.student_profile_id)
        if profile:
            profile_modifier = _get_profile_image_modifier(profile.name)

    def _build_prompt(base_prompt: str) -> str:
        if profile_modifier:
            return f"{base_prompt}. {profile_modifier}"
        return base_prompt

    def _slot_terms(*values: Optional[str]) -> str:
        return " ".join(str(v) for v in values if v)

    def _find_reusable_gallery_image(description: str, prompt: str) -> Optional[str]:
        needle = normalize_term(f"{description} {prompt}")
        if not needle:
            return None
        images = session.exec(select(GalleryImage).where(GalleryImage.style == style).limit(300)).all()
        if not images:
            images = session.exec(select(GalleryImage).limit(300)).all()
        for gallery_img in images:
            haystack = normalize_term(f"{gallery_img.description or ''} {gallery_img.prompt or ''}")
            if not haystack:
                continue
            if needle in haystack or haystack in needle:
                return gallery_img.image_url
            if any(len(part) > 3 and part in haystack for part in needle.split()):
                return gallery_img.image_url
        return None

    def _set_reused_image(slot: dict, url: str, prompt: str) -> None:
        if "generated" not in slot or not isinstance(slot["generated"], dict):
            slot["generated"] = {}
        slot["generated"][style] = {
            "image_url": url,
            "generated_at": datetime.utcnow().isoformat(),
            "prompt_used": prompt,
            "source": "gallery_reuse",
        }
        if slot.get("active_style", DEFAULT_IMAGE_STYLE) == style:
            slot["image_url"] = url

    def _set_pictogram(slot: dict, symbol: dict) -> None:
        apply_icon_symbol(slot, symbol)
        slot["active_style"] = "pictogram"
        if "generated" not in slot or not isinstance(slot["generated"], dict):
            slot["generated"] = {}
        slot["generated"]["pictogram"] = {
            "image_url": None,
            "generated_at": datetime.utcnow().isoformat(),
            "symbol": symbol.get("symbol"),
            "symbol_type": symbol.get("symbol_type"),
            "source": symbol.get("source"),
        }

    def _save_to_gallery(url: str, description: str, prompt: str) -> None:
        gallery_img = GalleryImage(
            image_url=url,
            description=description,
            source="generated",
            style=style,
            prompt=prompt[:500] if prompt else None,
            activity_id=adaptation.activity_id,
            adaptation_id=adaptation.id,
            user_id=current_user.id,
        )
        session.add(gallery_img)

    for img in output.get("image_options", []):
        symbol = find_icon_symbol(session, _slot_terms(img.get("description"), img.get("base_subject"), img.get("prompt")))
        if style == "pictogram" and symbol and not body.force:
            _set_pictogram(img, symbol)
            generated_count += 1
            continue
        if symbol and not body.force:
            apply_icon_symbol(img, symbol)
        # Skip symbol-illustrated slots unless explicitly forced
        if img.get("illustration_type") in {"emoji", "pictogram", "symbol"} and not body.force:
            continue
        already = (img.get("generated") or {}).get(style, {}).get("image_url")
        if already:
            continue
        base_prompt = (img.get("prompts") or {}).get(style) or img.get("prompt", "")
        if not base_prompt:
            continue
        prompt = _build_prompt(base_prompt)
        reused_url = _find_reusable_gallery_image(img.get("description", ""), prompt)
        if reused_url and not body.force:
            _set_reused_image(img, reused_url, prompt)
            continue
        if style == "pictogram":
            continue
        try:
            resp = await client.images.generate(
                model=model,
                prompt=prompt[:1000],
                size=size,
                n=1,
            )
            url = _save_image(resp.data[0])
            if "generated" not in img or not isinstance(img["generated"], dict):
                img["generated"] = {}
            img["generated"][style] = {
                "image_url": url,
                "generated_at": datetime.utcnow().isoformat(),
                "prompt_used": prompt,
            }
            if img.get("active_style", DEFAULT_IMAGE_STYLE) == style:
                img["image_url"] = url
            _save_to_gallery(url, img.get("description", "Imagem da atividade"), prompt)
            generated_count += 1
        except Exception as e:
            errors.append({"id": img.get("id", "?"), "error": _parse_image_error(str(e), openai_key)})

    for interaction in output.get("interaction_options", []):
        for item in interaction.get("items", []):
            if not isinstance(item, dict):
                continue
            symbol = find_icon_symbol(session, _slot_terms(item.get("name"), item.get("description"), item.get("image_prompt")))
            if style == "pictogram" and symbol and not body.force:
                _set_pictogram(item, symbol)
                generated_count += 1
                continue
            if symbol and not body.force:
                apply_icon_symbol(item, symbol)
            if item.get("illustration_type") in {"emoji", "pictogram", "symbol"} and not body.force:
                continue
            already = (item.get("generated") or {}).get(style, {}).get("image_url")
            if already:
                continue
            base_prompt = (item.get("prompts") or {}).get(style) or item.get("image_prompt", "")
            if not base_prompt:
                continue
            prompt = _build_prompt(base_prompt)
            reused_url = _find_reusable_gallery_image(item.get("name", ""), prompt)
            if reused_url and not body.force:
                _set_reused_image(item, reused_url, prompt)
                continue
            if style == "pictogram":
                continue
            try:
                resp = await client.images.generate(
                    model=model,
                    prompt=prompt[:1000],
                    size=size,
                    n=1,
                )
                url = _save_image(resp.data[0])
                if "generated" not in item or not isinstance(item["generated"], dict):
                    item["generated"] = {}
                item["generated"][style] = {
                    "image_url": url,
                    "generated_at": datetime.utcnow().isoformat(),
                    "prompt_used": prompt,
                }
                if item.get("active_style", DEFAULT_IMAGE_STYLE) == style:
                    item["image_url"] = url
                _save_to_gallery(url, item.get("name") or item.get("description") or "Item de interação", prompt)
                generated_count += 1
            except Exception as e:
                errors.append({"id": item.get("name", "?"), "error": _parse_image_error(str(e), openai_key)})

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()
    return {"status": "ok", "images_generated": generated_count, "errors": errors}


class ApplyGalleryImageRequest(BaseModel):
    slot_type: str  # "image_option" | "interaction_item"
    slot_id: str
    image_url: str
    gallery_image_id: Optional[str] = None
    style: Optional[str] = None


@router.post("/{adaptation_id}/apply-gallery-image")
def apply_gallery_image(
    adaptation_id: str,
    body: ApplyGalleryImageRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    import copy
    output = copy.deepcopy(adaptation.output_data or {})

    selected_style = body.style
    if body.gallery_image_id:
        gallery_image = session.get(GalleryImage, body.gallery_image_id)
        if gallery_image and gallery_image.style:
            selected_style = gallery_image.style
    selected_style = selected_style or DEFAULT_IMAGE_STYLE

    if body.slot_type == "image_option":
        for img in output.get("image_options", []):
            if img.get("id") == body.slot_id:
                img["image_url"] = body.image_url
                img["active_style"] = selected_style
                img["illustration_type"] = "generated"
                img.pop("emoji", None)
                img.pop("symbol", None)
                active_style = selected_style
                if "generated" not in img or not isinstance(img.get("generated"), dict):
                    img["generated"] = {}
                if active_style not in img["generated"] or not isinstance(img["generated"].get(active_style), dict):
                    img["generated"][active_style] = {}
                img["generated"][active_style]["image_url"] = body.image_url
                break

    elif body.slot_type == "interaction_item":
        for interaction in output.get("interaction_options", []):
            for item in interaction.get("items", []):
                if not isinstance(item, dict):
                    continue
                if item.get("name") == body.slot_id:
                    item["image_url"] = body.image_url
                    item["active_style"] = selected_style
                    item["illustration_type"] = "generated"
                    item.pop("emoji", None)
                    item.pop("symbol", None)
                    active_style = selected_style
                    if "generated" not in item or not isinstance(item.get("generated"), dict):
                        item["generated"] = {}
                    if active_style not in item["generated"] or not isinstance(item["generated"].get(active_style), dict):
                        item["generated"][active_style] = {}
                    item["generated"][active_style]["image_url"] = body.image_url
                    break

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()
    return {"status": "ok"}


class RegenerateImageRequest(BaseModel):
    slot_type: str  # "image_option" | "interaction_item"
    slot_id: str
    style: str = DEFAULT_IMAGE_STYLE
    feedback: str = ""


@router.post("/{adaptation_id}/regenerate-image")
async def regenerate_image(
    adaptation_id: str,
    body: RegenerateImageRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if body.style not in IMAGE_STYLES:
        raise HTTPException(status_code=400, detail=f"Estilo inválido: {body.style}")
    if body.style == "pictogram":
        raise HTTPException(status_code=400, detail="Pictograma usa a biblioteca de simbolos. Use Desenho ou Cartoon para gerar uma nova imagem com IA.")

    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    openai_key = get_user_openai_key(session, current_user.id)
    if not openai_key:
        raise HTTPException(status_code=400, detail="Chave OpenAI não configurada.")

    import copy
    from datetime import datetime

    style_cfg = IMAGE_STYLES[body.style]
    model = style_cfg["model"]
    size = style_cfg["size"]
    output = copy.deepcopy(adaptation.output_data or {})

    # Find original prompt and slot
    base_prompt = ""
    description = ""

    if body.slot_type == "image_option":
        for img in output.get("image_options", []):
            if img.get("id") == body.slot_id:
                base_prompt = (img.get("prompts") or {}).get(body.style) or img.get("prompt", "")
                description = img.get("description", "Imagem da atividade")
                break
    elif body.slot_type == "interaction_item":
        for interaction in output.get("interaction_options", []):
            for item in interaction.get("items", []):
                if isinstance(item, dict) and item.get("name") == body.slot_id:
                    base_prompt = (item.get("prompts") or {}).get(body.style) or item.get("image_prompt", "")
                    description = item.get("name", "Item de interação")
                    break

    if not base_prompt:
        raise HTTPException(status_code=400, detail="Prompt base não encontrado para esse slot.")

    # Combine base prompt with feedback modifier
    feedback_trimmed = body.feedback.strip()
    modified_prompt = f"{base_prompt}. {feedback_trimmed}" if feedback_trimmed else base_prompt

    client = make_openai_client(openai_key)
    try:
        resp = await client.images.generate(
            model=model,
            prompt=modified_prompt[:1000],
            size=size,
            n=1,
        )
        url = _save_image(resp.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=_parse_image_error(str(e), openai_key))

    # Save new image to gallery
    gallery_img = GalleryImage(
        image_url=url,
        description=f"{description} (feedback: {feedback_trimmed})" if feedback_trimmed else description,
        source="generated",
        style=body.style,
        prompt=modified_prompt[:500],
        activity_id=adaptation.activity_id,
        adaptation_id=adaptation.id,
        user_id=current_user.id,
    )
    session.add(gallery_img)

    # Update slot
    now_iso = datetime.utcnow().isoformat()
    if body.slot_type == "image_option":
        for img in output.get("image_options", []):
            if img.get("id") == body.slot_id:
                if "generated" not in img or not isinstance(img.get("generated"), dict):
                    img["generated"] = {}
                img["generated"][body.style] = {"image_url": url, "generated_at": now_iso}
                img["active_style"] = body.style
                img["illustration_type"] = "generated"
                img.pop("emoji", None)
                img.pop("symbol", None)
                img["image_url"] = url
                break
    elif body.slot_type == "interaction_item":
        for interaction in output.get("interaction_options", []):
            for item in interaction.get("items", []):
                if isinstance(item, dict) and item.get("name") == body.slot_id:
                    if "generated" not in item or not isinstance(item.get("generated"), dict):
                        item["generated"] = {}
                    item["generated"][body.style] = {"image_url": url, "generated_at": now_iso}
                    item["active_style"] = body.style
                    item["illustration_type"] = "generated"
                    item.pop("emoji", None)
                    item.pop("symbol", None)
                    item["image_url"] = url
                    break

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()
    return {"status": "ok", "image_url": url, "gallery_image_id": gallery_img.id}


@router.post("/{adaptation_id}/image-style")
def set_image_style(
    adaptation_id: str,
    body: SetImageStyleRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if body.style not in IMAGE_STYLES:
        raise HTTPException(status_code=400, detail=f"Estilo inválido. Opções: {list(IMAGE_STYLES.keys())}")

    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    import copy
    output = copy.deepcopy(adaptation.output_data or {})
    style = body.style

    for img in output.get("image_options", []):
        img["active_style"] = style
        img["is_active"] = img.get("id") in body.active_image_ids
        url = (img.get("generated") or {}).get(style, {}).get("image_url")
        img["image_url"] = url

    for interaction in output.get("interaction_options", []):
        for item in interaction.get("items", []):
            if not isinstance(item, dict):
                continue
            item["active_style"] = style
            url = (item.get("generated") or {}).get(style, {}).get("image_url")
            item["image_url"] = url

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()
    return {"status": "ok"}


@router.post("/{adaptation_id}/generate-audio")
async def generate_audio(
    adaptation_id: str,
    request: Request,
    force: bool = False,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    """Generate TTS audio for all audio_options scripts using OpenAI Speech API.

    Skips slots where audio_url is already set unless force=true.
    """
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")
    if not adaptation.output_data:
        raise HTTPException(status_code=400, detail="Adaptation has no output data.")

    openai_key = get_user_openai_key(session, current_user.id)
    if not openai_key:
        raise HTTPException(status_code=400, detail="Chave OpenAI não configurada. Acesse Configurações → Chaves de API.")

    import copy
    output = copy.deepcopy(adaptation.output_data)
    audio_options = output.get("audio_options", [])
    generated_count = 0
    errors = []

    for opt in audio_options:
        if opt.get("audio_url") and not force:
            continue
        tts_script = opt.get("tts_script") or opt.get("script", "")
        if not tts_script:
            continue
        voice = opt.get("voice", "alloy")
        rhythm = float(opt.get("rhythm", 1.0))
        try:
            url = await generate_audio_tts(openai_key, tts_script, voice, rhythm, str(request.base_url).rstrip("/"))
            opt["audio_url"] = url
            generated_count += 1
        except Exception as exc:
            errors.append({"id": opt.get("id"), "error": str(exc)})

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()

    return {
        "generated": generated_count,
        "errors": errors,
        "audio_options": audio_options,
    }


@router.get("/{adaptation_id}/pdf")
def download_adaptation_pdf(
    adaptation_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    """Generate and stream a WCAG-compliant A4 PDF for the given adaptation."""
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptação não encontrada")
    if not adaptation.output_data:
        raise HTTPException(status_code=422, detail="Adaptação ainda não tem conteúdo gerado")

    activity = session.get(Activity, adaptation.activity_id)
    title = activity.title if activity else "Atividade"
    discipline = activity.discipline if activity else None
    story = session.get(Story, activity.story_id) if activity and activity.story_id else None

    profile_name: Optional[str] = None
    if adaptation.student_profile_id:
        profile = session.get(StudentProfile, adaptation.student_profile_id)
        profile_name = profile.name if profile else None

    cfg = get_profile_config(profile_name)
    pdf_bytes = AdaptationPDFRenderer(
        output_data=normalized_output_data(adaptation.output_data, activity=_activity_math_context(activity)),
        activity_title=title,
        config=cfg,
        discipline=discipline,
        story_data=_story_pdf_data(story),
    ).render()

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60]
    filename = f"atividade_{safe_title}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
