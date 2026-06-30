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
from ..models.attempt import StudentActivityAttempt
from ..routes.auth import get_session_user
from ..routes.stories import serialize_story_detail
from ..services.static_url_service import normalized_output_data
from ..services.pdf_service import AdaptationPDFRenderer, build_combined_pdf
from ..services.pdf_constants import get_profile_config
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
    """True if student's profile matches the adaptation's profile."""
    if adaptation.student_id == student.id:
        return True
    if student.profile_id and adaptation.student_profile_id == student.profile_id:
        return True
    return False


def _get_item_label(item: object) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("name") or item.get("description") or str(item)
    return str(item)


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


def _calculate_score(adaptation_output: dict, response: dict) -> tuple[float, float]:
    try:
        interaction = adaptation_output.get("interaction_options", [{}])[0]
        items = interaction.get("items", [])
        correct_answer = interaction.get("correct_answer", {})
        interaction_type = interaction.get("type", "drag_and_drop")

        if not items:
            return 2.0, 4.0

        max_score = float(len(items))

        if interaction_type == "multiple_choice":
            chosen = next(iter(response.values()), None)
            correct_zone = correct_answer.get("correct_zone")
            return (max_score if chosen == correct_zone else 0.0), max_score

        if not correct_answer:
            # No answer key: give credit for all answered items
            labels = [_get_item_label(i) for i in items]
            answered = sum(1 for lbl in labels if response.get(lbl) is not None)
            return round((answered / len(labels)) * max_score, 2), max_score

        labels = [_get_item_label(i) for i in items]
        correct_count = sum(
            1 for lbl in labels
            if response.get(lbl) is not None and response.get(lbl) == correct_answer.get(lbl)
        )
        return round((correct_count / len(labels)) * max_score, 2), max_score
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

    adaptations = []
    if student.profile_id:
        adaptations = session.exec(
            select(ActivityAdaptation).where(
                ActivityAdaptation.student_profile_id == student.profile_id,
                ActivityAdaptation.status == "published",
            )
        ).all()

    direct_adaptations = session.exec(
        select(ActivityAdaptation).where(
            ActivityAdaptation.student_id == student.id,
            ActivityAdaptation.status == "published",
        )
    ).all()
    by_id = {a.id: a for a in adaptations}
    for a in direct_adaptations:
        by_id[a.id] = a
    adaptations = sorted(by_id.values(), key=lambda a: a.created_at, reverse=True)

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


@router.get("/activities/export-all-pdf")
def export_all_activities_pdf(
    current_user=Depends(get_session_user),
    session: Session = Depends(get_session),
):
    """Generate a multi-page PDF with all published activities for the student."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = _get_student(session, current_user.id)

    profile_name: Optional[str] = None
    if student.profile_id:
        profile = session.get(StudentProfile, student.profile_id)
        profile_name = profile.name if profile else None

    if student.profile_id:
        rows = session.exec(
            select(ActivityAdaptation).where(
                ActivityAdaptation.student_profile_id == student.profile_id,
                ActivityAdaptation.status == "published",
            )
        ).all()
    else:
        rows = session.exec(
            select(ActivityAdaptation).where(
                ActivityAdaptation.student_profile_id == None,
                ActivityAdaptation.status == "published",
            )
        ).all()

    if not rows:
        raise HTTPException(status_code=404, detail="No published activities found for this student")

    cfg = get_profile_config(profile_name)
    renderers = []
    for adaptation in rows:
        if not adaptation.output_data:
            continue
        activity = session.get(Activity, adaptation.activity_id)
        title = activity.title if activity else "Atividade"
        discipline = activity.discipline if activity else None
        story = session.get(Story, activity.story_id) if activity and activity.story_id else None
        renderers.append(AdaptationPDFRenderer(
            output_data=adaptation.output_data,
            activity_title=title,
            config=cfg,
            discipline=discipline,
            story_data=_story_pdf_data(story),
        ))

    if not renderers:
        raise HTTPException(status_code=404, detail="No activities with generated content found")

    pdf_bytes = build_combined_pdf(renderers)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="minhas_atividades.pdf"'},
    )


@router.get("/activities/{adaptation_id}")
def get_student_activity(
    adaptation_id: str,
    request: Request,
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
    story = session.get(Story, activity.story_id) if activity and activity.story_id else None
    return {
        "id": adaptation.id,
        "activity_id": adaptation.activity_id,
        "title": activity.title if activity else None,
        "story": serialize_story_detail(story, str(request.base_url).rstrip("/")),
        "output": normalized_output_data(adaptation.output_data, str(request.base_url).rstrip("/")),
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


@router.get("/activities/{adaptation_id}/pdf")
def download_student_activity_pdf(
    adaptation_id: str,
    current_user=Depends(get_session_user),
    session: Session = Depends(get_session),
):
    """Generate and download the PDF version of a published activity the student has access to."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    student = _get_student(session, current_user.id)
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation or adaptation.status != "published" or not _can_access(adaptation, student):
        raise HTTPException(status_code=404, detail="Activity not found or not published")
    if not adaptation.output_data:
        raise HTTPException(status_code=422, detail="Activity has no generated content yet")

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
        output_data=adaptation.output_data,
        activity_title=title,
        config=cfg,
        discipline=discipline,
        story_data=_story_pdf_data(story),
    ).render()

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'},
    )
