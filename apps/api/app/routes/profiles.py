from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.student_profile import StudentProfile
from ..models.adaptation import ActivityAdaptation
from ..models.activity import Activity
from ..routes.auth import get_session_user, require_role
import uuid

router = APIRouter(prefix="/student-profiles", tags=["profiles"])


class ProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    reading_level: Optional[str] = None
    autonomy_level: Optional[str] = None
    main_difficulties: Optional[List[str]] = None
    recommended_strategies: Optional[List[str]] = None
    preferred_modalities: Optional[List[str]] = None
    resources_to_avoid: Optional[List[str]] = None
    accessibility_complexity: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_profiles(
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    profiles = session.exec(
        select(StudentProfile).where(
            StudentProfile.teacher_id == current_user.id,
            StudentProfile.is_active == True,
        )
    ).all()
    return profiles


@router.post("", status_code=201)
def create_profile(
    body: ProfileCreate,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    profile = StudentProfile(id=str(uuid.uuid4()), teacher_id=current_user.id, **body.model_dump())
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/{profile_id}")
def get_profile(
    profile_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    profile = session.get(StudentProfile, profile_id)
    if not profile or profile.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/{profile_id}/adaptations")
def list_profile_adaptations(
    profile_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    profile = session.get(StudentProfile, profile_id)
    if not profile or profile.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Profile not found")

    adaptations = session.exec(
        select(ActivityAdaptation)
        .where(ActivityAdaptation.student_profile_id == profile_id)
        .order_by(ActivityAdaptation.created_at.desc())
    ).all()

    result = []
    for a in adaptations:
        activity = session.get(Activity, a.activity_id)
        result.append({
            "id": a.id,
            "activity_id": a.activity_id,
            "activity_title": activity.title if activity else None,
            "status": a.status,
            "version": a.version,
            "generated_by": a.generated_by,
            "created_at": str(a.created_at),
        })
    return result


@router.put("/{profile_id}")
def update_profile(
    profile_id: str,
    body: ProfileCreate,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    profile = session.get(StudentProfile, profile_id)
    if not profile or profile.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Profile not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(profile, k, v)
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
