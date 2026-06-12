import uuid
from .conftest import create_user, get_token, auth
from app.models.activity import Activity


def _make_activity(session, teacher_id: str) -> Activity:
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        title="Atividade Teste",
        discipline="Ciências",
        school_year="2º ano",
        statement="Observe os animais.",
        question="Onde vivem?",
        expected_answer="Peixe na água. Cachorro na terra.",
        activity_type="association",
        status="active",
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def test_list_activities_requires_auth(client):
    r = client.get("/activities")
    assert r.status_code == 401


def test_list_activities_returns_list(client, session):
    teacher = create_user(session, role="teacher")
    _make_activity(session, teacher.id)
    token = get_token(client, teacher.email)
    r = client.get("/activities", headers=auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_student_cannot_list_activities(client, session):
    student = create_user(session, role="student", suffix="s")
    token = get_token(client, student.email)
    r = client.get("/activities", headers=auth(token))
    assert r.status_code == 403


def test_get_activity_by_id(client, session):
    teacher = create_user(session, role="teacher", suffix="2")
    activity = _make_activity(session, teacher.id)
    token = get_token(client, teacher.email)
    r = client.get(f"/activities/{activity.id}", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["title"] == "Atividade Teste"
