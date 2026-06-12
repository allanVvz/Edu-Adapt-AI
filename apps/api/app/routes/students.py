from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.user import User
from ..models.student import Student, TeacherStudent
from ..models.student_profile import StudentProfile
from ..routes.auth import get_session_user, require_role
from ..services.auth_service import hash_password
import uuid

router = APIRouter(prefix="/students", tags=["students"])


class StudentCreate(BaseModel):
    name: str
    email: str
    password: str
    school_year: Optional[str] = None
    profile_id: Optional[str] = None
    learning_notes: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    school_year: Optional[str] = None
    profile_id: Optional[str] = None
    learning_notes: Optional[str] = None


def _student_response(user: User, student: Student, profile: Optional[StudentProfile] = None):
    return {
        "id": student.id,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "school_year": student.school_year,
        "learning_notes": student.learning_notes,
        "profile_id": student.profile_id,
        "profile_name": profile.name if profile else None,
        "created_at": student.created_at,
    }


@router.get("")
def list_students(
    current_user: User = Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if current_user.role == "admin":
        all_students = session.exec(select(Student)).all()
        result = []
        for student in all_students:
            user = session.get(User, student.user_id)
            if not user:
                continue
            profile = session.get(StudentProfile, student.profile_id) if student.profile_id else None
            teacher_link = session.exec(
                select(TeacherStudent).where(TeacherStudent.student_id == student.id)
            ).first()
            teacher_name = None
            if teacher_link:
                teacher_user = session.get(User, teacher_link.teacher_id)
                teacher_name = teacher_user.name if teacher_user else None
            r = _student_response(user, student, profile)
            r["teacher_name"] = teacher_name
            result.append(r)
        return result

    links = session.exec(
        select(TeacherStudent).where(TeacherStudent.teacher_id == current_user.id)
    ).all()
    result = []
    for link in links:
        student = session.get(Student, link.student_id)
        if not student:
            continue
        user = session.get(User, student.user_id)
        profile = session.get(StudentProfile, student.profile_id) if student.profile_id else None
        r = _student_response(user, student, profile)
        r["teacher_name"] = current_user.name
        result.append(r)
    return result


@router.post("", status_code=201)
def create_student(
    body: StudentCreate,
    current_user: User = Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        role="student",
    )
    session.add(user)
    session.flush()

    student = Student(
        id=str(uuid.uuid4()),
        user_id=user.id,
        profile_id=body.profile_id,
        school_year=body.school_year,
        learning_notes=body.learning_notes,
    )
    session.add(student)
    session.flush()

    session.add(TeacherStudent(
        id=str(uuid.uuid4()),
        teacher_id=current_user.id,
        student_id=student.id,
    ))
    session.commit()

    profile = session.get(StudentProfile, student.profile_id) if student.profile_id else None
    return _student_response(user, student, profile)


@router.get("/{student_id}")
def get_student(
    student_id: str,
    current_user: User = Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    user = session.get(User, student.user_id)
    profile = session.get(StudentProfile, student.profile_id) if student.profile_id else None
    return _student_response(user, student, profile)


@router.put("/{student_id}")
def update_student(
    student_id: str,
    body: StudentUpdate,
    current_user: User = Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user = session.get(User, student.user_id)
    if body.name:
        user.name = body.name
        session.add(user)

    if body.school_year is not None:
        student.school_year = body.school_year
    if body.profile_id is not None:
        student.profile_id = body.profile_id
    if body.learning_notes is not None:
        student.learning_notes = body.learning_notes
    student.updated_at = datetime.utcnow()
    session.add(student)
    session.commit()

    profile = session.get(StudentProfile, student.profile_id) if student.profile_id else None
    return _student_response(user, student, profile)
