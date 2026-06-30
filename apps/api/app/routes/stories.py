from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified
import copy
import uuid

from ..database import get_session
from ..models.story import Story
from ..models.user import User
from ..routes.auth import require_role
from ..services.openai_service import generate_audio_tts, get_user_openai_key
from ..services.static_url_service import normalize_static_urls


router = APIRouter(prefix="/stories", tags=["stories"])


class StoryCreate(BaseModel):
    title: str
    content: str
    audio_options: Optional[list] = None
    image_options: Optional[list] = None
    status: str = "active"


def _can_manage_story(story: Story, current_user: User) -> bool:
    return current_user.role == "admin" or story.teacher_id == current_user.id


def serialize_story_summary(story: Story | None) -> dict | None:
    if not story:
        return None
    return {
        "id": story.id,
        "title": story.title,
        "status": story.status,
    }


def serialize_story_detail(story: Story | None, api_base_url: str | None = None) -> dict | None:
    if not story:
        return None
    return {
        "id": story.id,
        "title": story.title,
        "content": story.content,
        "audio_options": normalize_static_urls(story.audio_options or [], api_base_url),
        "image_options": normalize_static_urls(story.image_options or [], api_base_url),
        "status": story.status,
        "created_at": story.created_at,
        "updated_at": story.updated_at,
    }


@router.get("")
def list_stories(
    status: Optional[str] = None,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if current_user.role == "admin":
        query = select(Story)
    else:
        query = select(Story).where(Story.teacher_id == current_user.id)
    if status:
        query = query.where(Story.status == status)
    rows = session.exec(query.order_by(Story.created_at.desc())).all()
    return [serialize_story_detail(row) for row in rows]


@router.post("", status_code=201)
def create_story(
    body: StoryCreate,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    story = Story(
        id=str(uuid.uuid4()),
        teacher_id=current_user.id,
        title=body.title,
        content=body.content,
        audio_options=body.audio_options,
        image_options=body.image_options,
        status=body.status,
    )
    session.add(story)
    session.commit()
    session.refresh(story)
    return serialize_story_detail(story)


@router.get("/{story_id}")
def get_story(
    story_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    story = session.get(Story, story_id)
    if not story or not _can_manage_story(story, current_user):
        raise HTTPException(status_code=404, detail="Story not found")
    return serialize_story_detail(story)


@router.put("/{story_id}")
def update_story(
    story_id: str,
    body: StoryCreate,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    story = session.get(Story, story_id)
    if not story or not _can_manage_story(story, current_user):
        raise HTTPException(status_code=404, detail="Story not found")

    story.title = body.title
    story.content = body.content
    story.audio_options = body.audio_options
    story.image_options = body.image_options
    story.status = body.status
    story.updated_at = datetime.utcnow()
    session.add(story)
    session.commit()
    session.refresh(story)
    return serialize_story_detail(story)


@router.post("/{story_id}/generate-audio")
async def generate_story_audio(
    story_id: str,
    request: Request,
    force: bool = False,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    story = session.get(Story, story_id)
    if not story or not _can_manage_story(story, current_user):
        raise HTTPException(status_code=404, detail="Story not found")

    openai_key = get_user_openai_key(session, current_user.id)
    if not openai_key:
        raise HTTPException(status_code=400, detail="Chave OpenAI não configurada.")

    audio_options = copy.deepcopy(story.audio_options or [])
    if not audio_options:
        audio_options = [{
            "id": "story_audio_1",
            "script": story.content,
            "tts_script": " ".join(story.content.split()),
            "voice_style": "calma",
            "voice": "shimmer",
            "rhythm": 0.85,
            "pitch": "normal",
            "audio_url": None,
            "source": "story",
        }]

    generated_count = 0
    errors = []
    for opt in audio_options:
        if opt.get("audio_url") and not force:
            continue
        tts_script = opt.get("tts_script") or opt.get("script") or story.content
        voice = opt.get("voice", "shimmer")
        rhythm = float(opt.get("rhythm", 0.85))
        try:
            opt["audio_url"] = await generate_audio_tts(
                openai_key,
                tts_script,
                voice,
                rhythm,
                str(request.base_url).rstrip("/"),
            )
            generated_count += 1
        except Exception as exc:
            errors.append({"id": opt.get("id"), "error": str(exc)})

    story.audio_options = audio_options
    flag_modified(story, "audio_options")
    story.updated_at = datetime.utcnow()
    session.add(story)
    session.commit()
    session.refresh(story)

    return {
        "generated": generated_count,
        "errors": errors,
        "audio_options": normalize_static_urls(story.audio_options or [], str(request.base_url).rstrip("/")),
    }
