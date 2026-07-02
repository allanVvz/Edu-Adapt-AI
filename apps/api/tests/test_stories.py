import uuid

from sqlmodel import select

from .conftest import create_user, get_token, auth
from app.models.activity import Activity
from app.models.adaptation import ActivityAdaptation
from app.models.api_key import ApiKey
from app.models.story import Story
from app.models.student import Student
from app.models.student_profile import StudentProfile
from app.seeds.seed_apostila_portugues import (
    RAVI_NINA_ACTIVITY_CODES,
    RAVI_NINA_STORY_TITLE,
    _seed_apostila_activities,
)
from app.seeds.seed_tea_activities import (
    ANA_STORY_TITLE,
    _seed_25_activities,
)
from app.services.openai_service import _mock_adaptation


def _make_story(session, teacher_id: str, title: str = "Conto Teste") -> Story:
    story = Story(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        title=title,
        content="Era uma vez um conto curto.",
        image_options=[{"id": "img_1", "description": "sol", "emoji": "☀️", "is_active": True}],
        audio_options=[{"id": "audio_1", "script": "Era uma vez.", "audio_url": None}],
        status="active",
    )
    session.add(story)
    session.commit()
    session.refresh(story)
    return story


def _make_student_with_profile(session, teacher_id: str):
    profile = StudentProfile(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        name="Perfil Teste",
    )
    student_user = create_user(session, role="student", suffix=str(uuid.uuid4())[:8])
    student = Student(
        id=str(uuid.uuid4()),
        user_id=student_user.id,
        profile_id=profile.id,
        school_year="2º ano",
    )
    session.add(profile)
    session.add(student)
    session.commit()
    session.refresh(profile)
    session.refresh(student)
    return student_user, student, profile


def _make_published_adaptation(session, teacher_id: str, profile_id: str, story_id: str) -> ActivityAdaptation:
    activity = Activity(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        story_id=story_id,
        title="Atividade com conto",
        statement="Leia o conto.",
        question="Quem aparece?",
        expected_answer="Personagem",
        activity_type="multiple_choice",
        status="active",
    )
    session.add(activity)
    session.flush()
    adaptation = ActivityAdaptation(
        id=str(uuid.uuid4()),
        activity_id=activity.id,
        student_profile_id=profile_id,
        generated_by="mock",
        output_data=_mock_adaptation(
            {
                "title": activity.title,
                "statement": activity.statement,
                "question": activity.question,
                "expected_answer": activity.expected_answer,
                "activity_type": activity.activity_type,
            },
            {},
        ),
        status="published",
    )
    session.add(adaptation)
    session.commit()
    session.refresh(adaptation)
    return adaptation


def test_story_crud_requires_teacher_or_admin(client, session):
    student = create_user(session, role="student", suffix="story")
    student_token = get_token(client, student.email)
    assert client.get("/stories", headers=auth(student_token)).status_code == 403

    teacher = create_user(session, role="teacher", suffix="story")
    teacher_token = get_token(client, teacher.email)
    response = client.post(
        "/stories",
        json={"title": "Meu conto", "content": "Texto do conto."},
        headers=auth(teacher_token),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Meu conto"
    assert body["content"] == "Texto do conto."


def test_teacher_can_create_activity_with_existing_story(client, session):
    teacher = create_user(session, role="teacher", suffix="link")
    story = _make_story(session, teacher.id)
    token = get_token(client, teacher.email)

    response = client.post(
        "/activities",
        json={
            "story_id": story.id,
            "title": "Atividade vinculada",
            "activity_type": "multiple_choice",
            "base_complexity": 2,
        },
        headers=auth(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["story_id"] == story.id


def test_teacher_cannot_link_story_from_other_teacher(client, session):
    owner = create_user(session, role="teacher", suffix="owner")
    other = create_user(session, role="teacher", suffix="other")
    story = _make_story(session, owner.id)
    token = get_token(client, other.email)

    response = client.post(
        "/activities",
        json={
            "story_id": story.id,
            "title": "Atividade proibida",
            "activity_type": "multiple_choice",
            "base_complexity": 2,
        },
        headers=auth(token),
    )

    assert response.status_code == 403


def test_student_activity_returns_story_when_activity_has_story(client, session):
    teacher = create_user(session, role="teacher", suffix="studentstory")
    story = _make_story(session, teacher.id, title="Conto Compartilhado")
    student_user, _student, profile = _make_student_with_profile(session, teacher.id)
    adaptation = _make_published_adaptation(session, teacher.id, profile.id, story.id)
    token = get_token(client, student_user.email)

    response = client.get(f"/student/activities/{adaptation.id}", headers=auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["story"]["id"] == story.id
    assert body["story"]["title"] == "Conto Compartilhado"
    assert body["story"]["image_options"][0]["emoji"] == "☀️"


def test_generate_story_audio_updates_audio_url(client, session, monkeypatch):
    fake_url = "http://test/static/audio/story.mp3"

    async def fake_tts(*args, **kwargs):
        return fake_url

    monkeypatch.setattr("app.routes.stories.generate_audio_tts", fake_tts)

    teacher = create_user(session, role="teacher", suffix="storyaudio")
    session.add(ApiKey(
        id=str(uuid.uuid4()),
        user_id=teacher.id,
        provider="openai",
        key_name="test",
        encrypted_value="sk-fake",
        status="active",
    ))
    story = _make_story(session, teacher.id, title="Conto com áudio")
    token = get_token(client, teacher.email)

    response = client.post(f"/stories/{story.id}/generate-audio", headers=auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["generated"] == 1
    assert body["audio_options"][0]["audio_url"].endswith("/static/audio/story.mp3")


def test_ravi_nina_seed_links_same_story_to_multiple_activities(client, session):
    teacher = create_user(session, role="teacher", suffix="ravi")
    for name in (
        "TEA — Apoio Visual e Leitura Inicial",
        "TEA — Hipersensibilidade Visual",
        "TEA — Não Verbal",
    ):
        session.add(StudentProfile(id=str(uuid.uuid4()), teacher_id=teacher.id, name=name))
    session.commit()

    profiles = {
        "p1": session.exec(select(StudentProfile).where(StudentProfile.name == "TEA — Apoio Visual e Leitura Inicial")).first(),
        "p2": session.exec(select(StudentProfile).where(StudentProfile.name == "TEA — Hipersensibilidade Visual")).first(),
        "p3": session.exec(select(StudentProfile).where(StudentProfile.name == "TEA — Não Verbal")).first(),
    }
    _seed_apostila_activities(session, teacher, profiles)

    story = session.exec(select(Story).where(Story.title == RAVI_NINA_STORY_TITLE)).first()
    assert story is not None

    activities = session.exec(select(Activity).where(Activity.story_id == story.id)).all()
    linked_titles = {activity.title for activity in activities}
    assert "Personagens do conto: O Coelho e a Chuva" in linked_titles
    assert "Sequência de acontecimentos: O Coelho e a Chuva" in linked_titles
    assert all("Pontua" not in title for title in linked_titles)
    assert len(activities) >= len(RAVI_NINA_ACTIVITY_CODES)
    assert {activity.story_id for activity in activities} == {story.id}


def test_ana_seed_links_story_context_to_ordering_activity(client, session):
    teacher = create_user(session, role="teacher", suffix="ana")
    for name in (
        "TEA â€” Apoio Visual e Leitura Inicial",
        "TEA â€” Hipersensibilidade Visual",
        "TEA â€” NÃ£o Verbal",
    ):
        session.add(StudentProfile(id=str(uuid.uuid4()), teacher_id=teacher.id, name=name))
    session.commit()

    profiles = {
        "p1": session.exec(select(StudentProfile).where(StudentProfile.name == "TEA â€” Apoio Visual e Leitura Inicial")).first(),
        "p2": session.exec(select(StudentProfile).where(StudentProfile.name == "TEA â€” Hipersensibilidade Visual")).first(),
        "p3": session.exec(select(StudentProfile).where(StudentProfile.name == "TEA â€” NÃ£o Verbal")).first(),
    }
    _seed_25_activities(session, teacher, profiles)

    story = session.exec(select(Story).where(Story.title == ANA_STORY_TITLE)).first()
    activity = session.exec(select(Activity).where(Activity.title.contains("Ana"))).first()

    assert story is not None
    assert activity is not None
    assert activity.story_id == story.id
    assert "Ana acordou cedo" in story.content
