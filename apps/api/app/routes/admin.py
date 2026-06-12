import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.user import User
from ..models.student import Student, TeacherStudent
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..routes.auth import require_role

router = APIRouter(prefix="/admin", tags=["admin"])


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherAssignment(BaseModel):
    teacher_id: str
    student_id: str


class AdaptationAssign(BaseModel):
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None


@router.get("/users")
def list_users(
    current_user=Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    users = session.exec(select(User).order_by(User.role, User.name)).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": str(u.created_at),
        }
        for u in users
    ]


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    body: UserUpdate,
    current_user=Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        if body.role not in ("admin", "teacher", "student"):
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.name is not None:
        user.name = body.name
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active}


@router.get("/overview")
def get_overview(
    current_user=Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Complete tree: teachers → students → activities → adaptations."""
    teachers = session.exec(select(User).where(User.role == "teacher")).all()
    teachers_data = []

    for teacher in teachers:
        links = session.exec(
            select(TeacherStudent).where(TeacherStudent.teacher_id == teacher.id)
        ).all()
        students_data = []
        for link in links:
            student = session.get(Student, link.student_id)
            if not student:
                continue
            student_user = session.get(User, student.user_id)

            adaptations = session.exec(
                select(ActivityAdaptation).where(
                    ActivityAdaptation.student_id == student.id
                )
            ).all()
            if student.profile_id:
                seen = {a.id for a in adaptations}
                for a in session.exec(
                    select(ActivityAdaptation).where(
                        ActivityAdaptation.student_profile_id == student.profile_id
                    )
                ).all():
                    if a.id not in seen:
                        adaptations.append(a)

            activity_map: dict = {}
            for adaptation in adaptations:
                activity = session.get(Activity, adaptation.activity_id)
                if not activity:
                    continue
                if activity.id not in activity_map:
                    activity_map[activity.id] = {
                        "activity": {
                            "id": activity.id,
                            "title": activity.title,
                            "discipline": activity.discipline,
                        },
                        "adaptations": [],
                    }
                activity_map[activity.id]["adaptations"].append({
                    "id": adaptation.id,
                    "status": adaptation.status,
                    "version": adaptation.version,
                    "created_at": str(adaptation.created_at),
                })

            students_data.append({
                "student": {
                    "id": student.id,
                    "user_id": student_user.id if student_user else None,
                    "name": student_user.name if student_user else "—",
                    "email": student_user.email if student_user else "—",
                    "school_year": student.school_year,
                },
                "activities": list(activity_map.values()),
            })

        teachers_data.append({
            "teacher": {"id": teacher.id, "name": teacher.name, "email": teacher.email},
            "students": students_data,
        })

    assigned_ids = {
        s["student"]["id"]
        for t in teachers_data
        for s in t["students"]
    }
    all_students = session.exec(select(Student)).all()
    unassigned = []
    for student in all_students:
        if student.id not in assigned_ids:
            su = session.get(User, student.user_id)
            unassigned.append({
                "id": student.id,
                "user_id": su.id if su else None,
                "name": su.name if su else "—",
                "email": su.email if su else "—",
                "school_year": student.school_year,
            })

    return {"teachers": teachers_data, "unassigned_students": unassigned}


@router.post("/assign-teacher", status_code=201)
def assign_teacher(
    body: TeacherAssignment,
    current_user=Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    teacher = session.get(User, body.teacher_id)
    student = session.get(Student, body.student_id)
    if not teacher or teacher.role not in ("teacher", "admin"):
        raise HTTPException(status_code=400, detail="Invalid teacher")
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    existing = session.exec(
        select(TeacherStudent).where(
            TeacherStudent.teacher_id == body.teacher_id,
            TeacherStudent.student_id == body.student_id,
        )
    ).first()
    if existing:
        return {"message": "Already assigned"}

    session.add(TeacherStudent(
        id=str(uuid.uuid4()),
        teacher_id=body.teacher_id,
        student_id=body.student_id,
    ))
    session.commit()
    return {"message": "Assigned"}


@router.put("/adaptations/{adaptation_id}/assign")
def assign_adaptation(
    adaptation_id: str,
    body: AdaptationAssign,
    current_user=Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    """Assign/reassign student and/or teacher to an existing adaptation."""
    adaptation = session.get(ActivityAdaptation, adaptation_id)
    if not adaptation:
        raise HTTPException(status_code=404, detail="Adaptation not found")

    if body.student_id is not None:
        if body.student_id == "":
            adaptation.student_id = None
        else:
            student = session.get(Student, body.student_id)
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            adaptation.student_id = body.student_id

    if body.teacher_id is not None and body.teacher_id != "":
        activity = session.get(Activity, adaptation.activity_id)
        if activity:
            teacher = session.get(User, body.teacher_id)
            if not teacher or teacher.role not in ("teacher", "admin"):
                raise HTTPException(status_code=400, detail="Invalid teacher")
            activity.teacher_id = body.teacher_id
            session.add(activity)

    session.add(adaptation)
    session.commit()
    return {"message": "Assigned", "student_id": adaptation.student_id}


@router.delete("/assign-teacher")
def unassign_teacher(
    teacher_id: str,
    student_id: str,
    current_user=Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    link = session.exec(
        select(TeacherStudent).where(
            TeacherStudent.teacher_id == teacher_id,
            TeacherStudent.student_id == student_id,
        )
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Assignment not found")
    session.delete(link)
    session.commit()
    return {"message": "Unassigned"}
