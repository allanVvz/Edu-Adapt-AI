import uuid
from .conftest import create_user, get_token, auth
from app.models.activity import Activity
from app.models.adaptation import ActivityAdaptation
from app.services.openai_service import _mock_adaptation


def _seed_adaptation(session, teacher_id: str, status: str = "review") -> ActivityAdaptation:
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        title="Atividade Seed",
        statement="Teste",
        question="Pergunta?",
        expected_answer="Resposta.",
        activity_type="association",
        status="active",
    )
    session.add(activity)
    session.flush()

    output = _mock_adaptation(
        {"title": activity.title, "statement": activity.statement, "question": activity.question,
         "expected_answer": activity.expected_answer, "activity_type": activity.activity_type},
        {},
    )
    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        generated_by="mock",
        output_data=output,
        status=status,
        version=1,
    )
    session.add(adaptation)
    session.commit()
    session.refresh(adaptation)
    return adaptation


def test_list_adaptations_requires_auth(client):
    r = client.get("/adaptations")
    assert r.status_code == 401


def test_list_adaptations_empty(client, session):
    teacher = create_user(session, role="teacher")
    token = get_token(client, teacher.email)
    r = client.get("/adaptations", headers=auth(token))
    assert r.status_code == 200
    assert r.json() == []


def test_list_adaptations_filtered_by_status(client, session):
    teacher = create_user(session, role="teacher", suffix="2")
    _seed_adaptation(session, teacher.id, status="review")
    _seed_adaptation(session, teacher.id, status="approved")
    token = get_token(client, teacher.email)

    r_review = client.get("/adaptations?status=review", headers=auth(token))
    assert r_review.status_code == 200
    assert all(a["status"] == "review" for a in r_review.json())

    r_approved = client.get("/adaptations?status=approved", headers=auth(token))
    assert r_approved.status_code == 200
    assert all(a["status"] == "approved" for a in r_approved.json())


def test_get_adaptation_by_id(client, session):
    teacher = create_user(session, role="teacher", suffix="3")
    adaptation = _seed_adaptation(session, teacher.id)
    token = get_token(client, teacher.email)
    r = client.get(f"/adaptations/{adaptation.id}", headers=auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == adaptation.id
    assert "output" in body


def test_approve_adaptation(client, session):
    teacher = create_user(session, role="teacher", suffix="4")
    adaptation = _seed_adaptation(session, teacher.id, status="review")
    token = get_token(client, teacher.email)
    r = client.post(f"/adaptations/{adaptation.id}/approve", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_reject_adaptation(client, session):
    teacher = create_user(session, role="teacher", suffix="5")
    adaptation = _seed_adaptation(session, teacher.id, status="review")
    token = get_token(client, teacher.email)
    r = client.post(
        f"/adaptations/{adaptation.id}/reject",
        json={"feedback": "Precisa de mais imagens."},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_publish_adaptation(client, session):
    teacher = create_user(session, role="teacher", suffix="6")
    adaptation = _seed_adaptation(session, teacher.id, status="approved")
    token = get_token(client, teacher.email)
    r = client.post(f"/adaptations/{adaptation.id}/publish", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["status"] == "published"
