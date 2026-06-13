from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.user import User
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..models.student_profile import StudentProfile
from ..routes.auth import require_role
from ..services.openai_service import get_user_openai_key
from ..agents.orchestrator import run_adaptation_pipeline
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


@router.get("")
def list_activities(
    status: Optional[str] = None,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if current_user.role == "admin":
        query = select(Activity)
    else:
        query = select(Activity).where(Activity.teacher_id == current_user.id)

    if status:
        query = query.where(Activity.status == status)

    activities = session.exec(query.order_by(Activity.created_at.desc())).all()

    result = []
    for a in activities:
        all_adaptations = session.exec(
            select(ActivityAdaptation).where(ActivityAdaptation.activity_id == a.id)
        ).all()
        teacher_name = None
        if current_user.role == "admin":
            t = session.get(User, a.teacher_id)
            teacher_name = t.name if t else None
        result.append({
            "id": a.id,
            "title": a.title,
            "discipline": a.discipline,
            "school_year": a.school_year,
            "activity_type": a.activity_type,
            "base_complexity": a.base_complexity,
            "status": a.status,
            "teacher_id": a.teacher_id,
            "teacher_name": teacher_name,
            "adaptation_total": len(all_adaptations),
            "adaptation_pending": len([x for x in all_adaptations if x.status == "review"]),
            "adaptation_published": len([x for x in all_adaptations if x.status == "published"]),
            "created_at": str(a.created_at),
        })
    return result


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
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if current_user.role != "admin" and activity.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your activity")

    activity_dict = {
        "title": activity.title,
        "discipline": activity.discipline,
        "school_year": activity.school_year,
        "pedagogical_objective": activity.pedagogical_objective,
        "activity_type": activity.activity_type,
        "statement": activity.statement,
        "question": activity.question,
        "expected_answer": activity.expected_answer,
        "base_complexity": activity.base_complexity,
        "teacher_notes": activity.teacher_notes,
    }

    profile_dict: dict = {}
    if body.profile_id:
        profile = session.get(StudentProfile, body.profile_id)
        if profile:
            profile_dict = {
                "name": profile.name,
                "reading_level": profile.reading_level,
                "autonomy_level": profile.autonomy_level,
                "main_difficulties": profile.main_difficulties,
                "recommended_strategies": profile.recommended_strategies,
                "preferred_modalities": profile.preferred_modalities,
                "resources_to_avoid": profile.resources_to_avoid,
                "accessibility_complexity": profile.accessibility_complexity,
                "notes": profile.notes,
            }

    openai_key = get_user_openai_key(session, current_user.id)
    output = await run_adaptation_pipeline(activity_dict, profile_dict, openai_key)
    generated_by = "openai" if openai_key else "mock"

    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity_id,
        student_profile_id=body.profile_id,
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
