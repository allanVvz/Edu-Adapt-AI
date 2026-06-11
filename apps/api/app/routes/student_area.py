from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.adaptation import ActivityAdaptation
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


def _calculate_score(adaptation_output: dict, response: dict) -> tuple[float, float]:
    """Simple scoring for drag-and-drop association activities."""
    max_score = 4.0
    try:
        interaction = adaptation_output.get("interaction_options", [{}])[0]
        items = interaction.get("items", [])
        zones = interaction.get("zones", [])
        if not items:
            return 2.0, 4.0
        correct = sum(1 for item in items if response.get(item) is not None)
        score = (correct / len(items)) * max_score
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
    adaptations = session.exec(
        select(ActivityAdaptation).where(
            ActivityAdaptation.student_id == student.id,
            ActivityAdaptation.status == "published",
        )
    ).all()
    return [
        {
            "id": a.id,
            "activity_id": a.activity_id,
            "status": a.status,
            "created_at": a.created_at,
        }
        for a in adaptations
    ]


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
    if not adaptation or adaptation.student_id != student.id or adaptation.status != "published":
        raise HTTPException(status_code=404, detail="Activity not found or not published")

    return {
        "id": adaptation.id,
        "activity_id": adaptation.activity_id,
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
    if not adaptation or adaptation.student_id != student.id:
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
    if not adaptation or adaptation.student_id != student.id:
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
