from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..models.student_profile import StudentProfile
from ..routes.auth import require_role
from ..services.openai_service import get_user_openai_key, generate_adaptation_with_ai, _mock_adaptation
import uuid

router = APIRouter(prefix="/activities", tags=["activities"])


class ActivityCreate(BaseModel):
    title: str
    discipline: Optional[str] = None
    school_year: Optional[str] = None
    pedagogical_objective: Optional[str] = None
    bncc_skill: Optional[str] = None
    activity_type: Optional[str] = None
    statement: Optional[str] = None
    question: Optional[str] = None
    expected_answer: Optional[str] = None
    correction_criteria: Optional[str] = None
    base_complexity: int = 2
    original_modality: Optional[str] = None
    teacher_notes: Optional[str] = None


class AdaptRequest(BaseModel):
    profile_id: Optional[str] = None
    student_id: Optional[str] = None


@router.get("")
def list_activities(
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    activities = session.exec(
        select(Activity).where(Activity.teacher_id == current_user.id)
    ).all()
    return activities


@router.post("", status_code=201)
def create_activity(
    body: ActivityCreate,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    activity = Activity(id=str(uuid.uuid4()), teacher_id=current_user.id, **body.model_dump())
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


@router.get("/{activity_id}")
def get_activity(
    activity_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    activity = session.get(Activity, activity_id)
    if not activity or activity.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.put("/{activity_id}")
def update_activity(
    activity_id: str,
    body: ActivityCreate,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    activity = session.get(Activity, activity_id)
    if not activity or activity.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(activity, k, v)
    activity.updated_at = datetime.utcnow()
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


@router.post("/{activity_id}/adapt", status_code=201)
async def adapt_activity(
    activity_id: str,
    body: AdaptRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    activity = session.get(Activity, activity_id)
    if not activity or activity.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity_dict = {
        "title": activity.title,
        "statement": activity.statement,
        "question": activity.question,
        "expected_answer": activity.expected_answer,
        "activity_type": activity.activity_type,
    }

    profile_dict = {}
    if body.profile_id:
        profile = session.get(StudentProfile, body.profile_id)
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

    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity_id,
        student_profile_id=body.profile_id,
        student_id=body.student_id,
        generated_by=generated_by,
        output_data=output,
        status="review",
    )
    session.add(adaptation)
    session.commit()
    session.refresh(adaptation)

    return {
        "id": adaptation.id,
        "activity_id": adaptation.activity_id,
        "generated_by": adaptation.generated_by,
        "status": adaptation.status,
        "output": adaptation.output_data,
        "no_openai_key": not bool(openai_key),
    }
