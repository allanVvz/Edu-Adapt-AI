from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.adaptation import ActivityAdaptation
from ..models.activity import Activity
from ..models.student import Student
from ..models.attempt import StudentActivityAttempt
from ..routes.auth import get_session_user
import uuid

router = APIRouter(prefix="/student", tags=["student"])


class SubmitRequest(BaseModel):
    response: dict
    completion_time_seconds: Optional[int] = None


def _get_student(session: Session, user_id: str) -> Student:
    student = session.exec(select(Student).where(Student.user_id == user_id)).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    return student


def _can_access(adaptation: ActivityAdaptation, student: Student) -> bool:
    """True if student has direct assignment or matching profile."""
    if adaptation.student_id == student.id:
        return True
    if adaptation.student_id is None and student.profile_id and adaptation.student_profile_id == student.profile_id:
        return True
    return False


def _get_item_label(item: object) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("name", str(item))
    return str(item)


def _calculate_score(adaptation_output: dict, response: dict) -> tuple[float, float]:
    max_score = 4.0
    try:
        interaction = adaptation_output.get("interaction_options", [{}])[0]
        items = interaction.get("items", [])
        if not items:
            return 2.0, 4.0
        labels = [_get_item_label(i) for i in items]
        correct = sum(1 for label in labels if response.get(label) is not None)
        score = (correct / len(labels)) * max_score
        return round(score, 2), max_score
    except Exception:
        return 2.0, 4.0


@router.get("/activities")
def list_student_activities(
    current_user=Depends(get_session_user),
    session: Session = Depends(get_session),
):
    if current_user.role not in ("student",):
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = _get_student(session, current_user.id)

    # Direct assignments
    direct = session.exec(
        select(ActivityAdaptation).where(
            ActivityAdaptation.student_id == student.id,
            ActivityAdaptation.status == "published",
        )
    ).all()

    # Profile-based (student_id not set, but profile matches)
    profile_based = []
    if student.profile_id:
        profile_based = session.exec(
            select(ActivityAdaptation).where(
                ActivityAdaptation.student_profile_id == student.profile_id,
                ActivityAdaptation.student_id == None,
                ActivityAdaptation.status == "published",
            )
        ).all()

    seen = {a.id for a in direct}
    adaptations = direct + [a for a in profile_based if a.id not in seen]

    result = []
    for a in adaptations:
        activity = session.get(Activity, a.activity_id)
        result.append({
            "id": a.id,
            "activity_id": a.activity_id,
            "title": activity.title if activity else None,
            "status": a.status,
            "created_at": a.created_at,
        })
    return result


@router.get("/activities/{adaptation_id}")
def get_student_activity(
    adaptation_id: str,
    current_user=Depends(get_session_user),
    session: Session = Depends(get_session),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = _get_student(session, current_user.id)
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation or adaptation.status != "published" or not _can_access(adaptation, student):
        raise HTTPException(status_code=404, detail="Activity not found or not published")

    activity = session.get(Activity, adaptation.activity_id)
    return {
        "id": adaptation.id,
        "activity_id": adaptation.activity_id,
        "title": activity.title if activity else None,
        "output": adaptation.output_data,
    }


@router.post("/activities/{adaptation_id}/start")
def start_activity(
    adaptation_id: str,
    current_user=Depends(get_session_user),
    session: Session = Depends(get_session),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = _get_student(session, current_user.id)
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation or not _can_access(adaptation, student):
        raise HTTPException(status_code=404, detail="Activity not found")

    attempt = StudentActivityAttempt(
        id=str(uuid.uuid4()),
        student_id=student.id,
        activity_id=adaptation.activity_id,
        adaptation_id=adaptation_id,
        started_at=datetime.utcnow(),
        status="started",
    )
    session.add(attempt)
    session.commit()
    return {"attempt_id": attempt.id}


@router.post("/activities/{adaptation_id}/submit")
def submit_activity(
    adaptation_id: str,
    body: SubmitRequest,
    current_user=Depends(get_session_user),
    session: Session = Depends(get_session),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = _get_student(session, current_user.id)
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation or not _can_access(adaptation, student):
        raise HTTPException(status_code=404, detail="Activity not found")

    score, max_score = _calculate_score(adaptation.output_data or {}, body.response)

    attempt = session.exec(
        select(StudentActivityAttempt).where(
            StudentActivityAttempt.adaptation_id == adaptation_id,
            StudentActivityAttempt.student_id == student.id,
            StudentActivityAttempt.status == "started",
        )
    ).first()

    if attempt:
        attempt.finished_at = datetime.utcnow()
        attempt.status = "completed"
        attempt.raw_response = body.response
        attempt.score = score
        attempt.max_score = max_score
        attempt.completion_time_seconds = body.completion_time_seconds
        session.add(attempt)
    else:
        attempt = StudentActivityAttempt(
            id=str(uuid.uuid4()),
            student_id=student.id,
            activity_id=adaptation.activity_id,
            adaptation_id=adaptation_id,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            status="completed",
            raw_response=body.response,
            score=score,
            max_score=max_score,
            completion_time_seconds=body.completion_time_seconds,
        )
        session.add(attempt)

    session.commit()
    return {"score": score, "max_score": max_score, "percentage": round((score / max_score) * 100)}
