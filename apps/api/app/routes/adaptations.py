from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.adaptation import ActivityAdaptation
from ..models.activity import Activity
from ..models.student_profile import StudentProfile
from ..routes.auth import require_role
from ..services.openai_service import get_user_openai_key, generate_adaptation_with_ai, _mock_adaptation
import uuid

router = APIRouter(prefix="/adaptations", tags=["adaptations"])


class FeedbackRequest(BaseModel):
    feedback: Optional[str] = None


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

    return {
        "id": adaptation.id,
        "activity": {"id": activity.id, "title": activity.title} if activity else None,
        "profile": {"id": profile.id, "name": profile.name} if profile else None,
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
    if adaptation.status not in ("approved", "review"):
        raise HTTPException(status_code=400, detail="Adaptation must be approved before publishing")
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
