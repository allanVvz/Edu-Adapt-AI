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
from ..services.openai_service import get_user_openai_key, generate_adaptation_with_ai, _mock_adaptation, IMAGE_STYLES, VALID_IMAGE_MODELS
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

    from openai import AsyncOpenAI
    import copy
    from datetime import datetime

    client = AsyncOpenAI(api_key=openai_key)
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

    for img in output.get("image_options", []):
        already = (img.get("generated") or {}).get(style, {}).get("image_url")
        if already:
            continue
        prompt = (img.get("prompts") or {}).get(style) or img.get("prompt", "")
        if not prompt:
            continue
        try:
            resp = await client.images.generate(
                model=model,
                prompt=prompt[:1000],
                size=size,
                n=1,
            )
            url = resp.data[0].url
            if "generated" not in img or not isinstance(img["generated"], dict):
                img["generated"] = {}
            img["generated"][style] = {"image_url": url, "generated_at": datetime.utcnow().isoformat()}
            if img.get("active_style", "cartoon_2d") == style:
                img["image_url"] = url
            generated_count += 1
        except Exception as e:
            errors.append({"id": img.get("id", "?"), "error": str(e)})

    for interaction in output.get("interaction_options", []):
        for item in interaction.get("items", []):
            if not isinstance(item, dict):
                continue
            already = (item.get("generated") or {}).get(style, {}).get("image_url")
            if already:
                continue
            prompt = (item.get("prompts") or {}).get(style) or item.get("image_prompt", "")
            if not prompt:
                continue
            try:
                resp = await client.images.generate(
                    model=model,
                    prompt=prompt[:1000],
                    size=size,
                    n=1,
                )
                url = resp.data[0].url
                if "generated" not in item or not isinstance(item["generated"], dict):
                    item["generated"] = {}
                item["generated"][style] = {"image_url": url, "generated_at": datetime.utcnow().isoformat()}
                if item.get("active_style", "cartoon_2d") == style:
                    item["image_url"] = url
                generated_count += 1
            except Exception as e:
                errors.append({"id": item.get("name", "?"), "error": str(e)})

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()
    return {"status": "ok", "images_generated": generated_count, "errors": errors}


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
