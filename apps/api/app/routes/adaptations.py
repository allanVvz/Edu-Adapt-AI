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
from ..services.openai_service import get_user_openai_key, generate_adaptation_with_ai, _mock_adaptation
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


@router.post("/{adaptation_id}/generate-images")
async def generate_images(
    adaptation_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    openai_key = get_user_openai_key(session, current_user.id)
    if not openai_key:
        raise HTTPException(status_code=400, detail="Chave OpenAI não configurada. Acesse Configurações → Chaves de API.")

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=openai_key)

    output = dict(adaptation.output_data or {})
    generated = 0

    for img in output.get("image_options", []):
        if img.get("image_url") or not img.get("prompt"):
            continue
        try:
            resp = await client.images.generate(
                model="dall-e-2",
                prompt=img["prompt"][:1000],
                size="512x512",
                n=1,
            )
            img["image_url"] = resp.data[0].url
            generated += 1
        except Exception:
            pass

    for interaction in output.get("interaction_options", []):
        for item in interaction.get("items", []):
            if not isinstance(item, dict):
                continue
            if item.get("image_url") or not item.get("image_prompt"):
                continue
            try:
                resp = await client.images.generate(
                    model="dall-e-2",
                    prompt=item["image_prompt"][:1000],
                    size="256x256",
                    n=1,
                )
                item["image_url"] = resp.data[0].url
                generated += 1
            except Exception:
                pass

    adaptation.output_data = output
    session.add(adaptation)
    session.commit()
    return {"status": "ok", "images_generated": generated}
