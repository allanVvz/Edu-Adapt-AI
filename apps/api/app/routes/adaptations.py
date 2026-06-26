from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.adaptation import ActivityAdaptation
from ..models.activity import Activity
from ..models.student import Student
from ..models.student_profile import StudentProfile
from ..models.user import User
from ..routes.auth import require_role
from ..services.openai_service import get_user_openai_key, generate_adaptation_with_ai, _mock_adaptation, IMAGE_STYLES, VALID_IMAGE_MODELS, _parse_image_error, _save_image, _get_profile_image_modifier, generate_audio_tts, make_openai_client
from ..models.gallery_image import GalleryImage
from ..services.icon_symbol_service import apply_icon_symbol, find_icon_symbol, normalize_term
import uuid

router = APIRouter(prefix="/adaptations", tags=["adaptations"])


class FeedbackRequest(BaseModel):
    feedback: Optional[str] = None


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
        "output": adaptation.output_data,
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


class GenerateImagesRequest(BaseModel):
    style: str = "cartoon_2d"
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
    if not openai_key:
        raise HTTPException(status_code=400, detail="Chave OpenAI não configurada. Acesse Configurações → Chaves de API.")

    import copy
    from datetime import datetime

    client = make_openai_client(openai_key)
    style = body.style
    style_cfg = IMAGE_STYLES[style]
    model = style_cfg["model"]
    size = style_cfg["size"]

    # Guard: reject if model is not in the known-valid list
    if model not in VALID_IMAGE_MODELS:
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
        if slot.get("active_style", "cartoon_2d") == style:
            slot["image_url"] = url

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
            if img.get("active_style", "cartoon_2d") == style:
                img["image_url"] = url
            _save_to_gallery(url, img.get("description", "Imagem da atividade"), prompt)
            generated_count += 1
        except Exception as e:
            errors.append({"id": img.get("id", "?"), "error": _parse_image_error(str(e), openai_key)})

    for interaction in output.get("interaction_options", []):
        for item in interaction.get("items", []):
            if not isinstance(item, dict):
                continue
            symbol = find_icon_symbol(session, _slot_terms(item.get("name"), item.get("image_prompt")))
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
                if item.get("active_style", "cartoon_2d") == style:
                    item["image_url"] = url
                _save_to_gallery(url, item.get("name", "Item de interação"), prompt)
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

    if body.slot_type == "image_option":
        for img in output.get("image_options", []):
            if img.get("id") == body.slot_id:
                img["image_url"] = body.image_url
                active_style = img.get("active_style", "cartoon_2d")
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
                    active_style = item.get("active_style", "cartoon_2d")
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
    style: str = "cartoon_2d"
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
                if img.get("active_style", "cartoon_2d") == body.style:
                    img["image_url"] = url
                break
    elif body.slot_type == "interaction_item":
        for interaction in output.get("interaction_options", []):
            for item in interaction.get("items", []):
                if isinstance(item, dict) and item.get("name") == body.slot_id:
                    if "generated" not in item or not isinstance(item.get("generated"), dict):
                        item["generated"] = {}
                    item["generated"][body.style] = {"image_url": url, "generated_at": now_iso}
                    if item.get("active_style", "cartoon_2d") == body.style:
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
            url = await generate_audio_tts(openai_key, tts_script, voice, rhythm)
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
