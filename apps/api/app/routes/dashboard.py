from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from ..database import get_session
from ..models.student import Student, TeacherStudent
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..models.attempt import StudentActivityAttempt
from ..routes.auth import require_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/teacher")
def teacher_dashboard(
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    teacher_id = current_user.id

    total_students = session.exec(
        select(func.count(TeacherStudent.id)).where(TeacherStudent.teacher_id == teacher_id)
    ).one()

    total_activities = session.exec(
        select(func.count(Activity.id)).where(Activity.teacher_id == teacher_id)
    ).one()

    published_adaptations = session.exec(
        select(ActivityAdaptation).where(
            ActivityAdaptation.student_id.in_(
                select(Student.id).where(
                    Student.id.in_(
                        select(TeacherStudent.student_id).where(TeacherStudent.teacher_id == teacher_id)
                    )
                )
            ),
            ActivityAdaptation.status == "published",
        )
    ).all()

    pending_adaptations = session.exec(
        select(func.count(ActivityAdaptation.id)).where(
            ActivityAdaptation.activity_id.in_(
                select(Activity.id).where(Activity.teacher_id == teacher_id)
            ),
            ActivityAdaptation.status == "review",
        )
    ).one()

    recent_attempts = session.exec(
        select(StudentActivityAttempt)
        .where(
            StudentActivityAttempt.activity_id.in_(
                select(Activity.id).where(Activity.teacher_id == teacher_id)
            )
        )
        .order_by(StudentActivityAttempt.created_at.desc())
        .limit(10)
    ).all()

    scores = [a.score for a in recent_attempts if a.score is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    return {
        "total_students": total_students,
        "total_activities": total_activities,
        "published_adaptations": len(published_adaptations),
        "pending_adaptations": pending_adaptations,
        "avg_score": avg_score,
        "recent_attempts": [
            {
                "id": a.id,
                "student_id": a.student_id,
                "activity_id": a.activity_id,
                "score": a.score,
                "max_score": a.max_score,
                "status": a.status,
                "created_at": a.created_at,
            }
            for a in recent_attempts
        ],
    }
