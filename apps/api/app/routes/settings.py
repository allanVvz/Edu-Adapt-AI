from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models.user import User
from ..models.api_key import ApiKey
from ..routes.auth import get_session_user
import uuid

router = APIRouter(prefix="/settings", tags=["settings"])


class UpdateMeRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class ApiKeyCreate(BaseModel):
    provider: str
    key_name: str
    value: str


@router.get("/me")
def get_me(current_user: User = Depends(get_session_user)):
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email, "role": current_user.role}


@router.put("/me")
def update_me(
    body: UpdateMeRequest,
    current_user: User = Depends(get_session_user),
    session: Session = Depends(get_session),
):
    if body.name:
        current_user.name = body.name
    if body.email:
        current_user.email = body.email
    if body.password:
        from ..services.auth_service import hash_password
        current_user.hashed_password = hash_password(body.password)
    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}


@router.get("/api-keys")
def list_api_keys(current_user: User = Depends(get_session_user), session: Session = Depends(get_session)):
    keys = session.exec(select(ApiKey).where(ApiKey.user_id == current_user.id)).all()
    return [
        {"id": k.id, "provider": k.provider, "key_name": k.key_name, "status": k.status, "created_at": k.created_at}
        for k in keys
    ]


@router.post("/api-keys", status_code=201)
def create_api_key(
    body: ApiKeyCreate,
    current_user: User = Depends(get_session_user),
    session: Session = Depends(get_session),
):
    # Replace existing key for same provider
    existing = session.exec(
        select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.provider == body.provider)
    ).first()
    if existing:
        existing.encrypted_value = body.value  # NOTE: encrypt before production
        existing.key_name = body.key_name
        existing.status = "active"
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"id": existing.id, "provider": existing.provider, "key_name": existing.key_name}

    key = ApiKey(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        provider=body.provider,
        key_name=body.key_name,
        encrypted_value=body.value,
    )
    session.add(key)
    session.commit()
    return {"id": key.id, "provider": key.provider, "key_name": key.key_name}


@router.post("/api-keys/{key_id}/test-images")
async def test_api_key_images(
    key_id: str,
    current_user: User = Depends(get_session_user),
    session: Session = Depends(get_session),
):
    """Try to generate a real image with gpt-image-1 to validate the key has image access."""
    key = session.get(ApiKey, key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API key not found")
    if key.provider != "openai":
        raise HTTPException(status_code=400, detail="Teste de imagem é apenas para chaves OpenAI.")

    from openai import AsyncOpenAI
    from ..services.openai_service import IMAGE_STYLES, _parse_image_error, _save_image

    image_model = next(iter(IMAGE_STYLES.values()))["model"]
    client = AsyncOpenAI(api_key=key.encrypted_value)

    try:
        resp = await client.images.generate(
            model=image_model,
            prompt="A simple blue circle on a white background, minimal illustration, educational",
            size="1024x1024",
            n=1,
        )
        url = _save_image(resp.data[0])
        return {"ok": True, "model": image_model, "url": url}
    except Exception as e:
        hint = _parse_image_error(str(e), key.encrypted_value)
        return {"ok": False, "model": image_model, "error": str(e), "hint": hint}


@router.delete("/api-keys/{key_id}", status_code=204)
def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_session_user),
    session: Session = Depends(get_session),
):
    key = session.get(ApiKey, key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API key not found")
    session.delete(key)
    session.commit()
