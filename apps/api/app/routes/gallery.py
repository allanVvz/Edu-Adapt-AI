import os
import uuid as _uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlmodel import Session, select
from ..database import get_session
from ..models.gallery_image import GalleryImage
from ..routes.auth import require_role
from ..services.openai_service import _STATIC_DIR, _API_BASE_URL

router = APIRouter(prefix="/gallery", tags=["gallery"])


class UpdateDescriptionRequest(BaseModel):
    description: str


@router.get("")
def list_gallery(
    search: Optional[str] = None,
    style: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 200,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    query = select(GalleryImage).order_by(GalleryImage.created_at.desc())
    if style:
        query = query.where(GalleryImage.style == style)
    if source:
        query = query.where(GalleryImage.source == source)
    images = session.exec(query.limit(limit)).all()
    if search:
        s = search.lower()
        images = [img for img in images
                  if s in (img.description or "").lower() or s in (img.prompt or "").lower()]
    return [
        {
            "id": img.id,
            "image_url": img.image_url,
            "description": img.description,
            "source": img.source,
            "style": img.style,
            "prompt": img.prompt,
            "activity_id": img.activity_id,
            "adaptation_id": img.adaptation_id,
            "created_at": img.created_at,
        }
        for img in images
    ]


@router.post("/upload", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    description: str = Form(...),
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem (PNG, JPG, etc).")

    ext = "png"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "webp", "gif"):
        ext = "png"

    os.makedirs(_STATIC_DIR, exist_ok=True)
    filename = f"{_uuid.uuid4()}.{ext}"
    filepath = f"{_STATIC_DIR}/{filename}"

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    image_url = f"{_API_BASE_URL}/static/images/{filename}"
    gallery_img = GalleryImage(
        image_url=image_url,
        description=description.strip(),
        source="uploaded",
        user_id=current_user.id,
    )
    session.add(gallery_img)
    session.commit()
    session.refresh(gallery_img)
    return {
        "id": gallery_img.id,
        "image_url": gallery_img.image_url,
        "description": gallery_img.description,
        "source": gallery_img.source,
        "style": gallery_img.style,
        "created_at": gallery_img.created_at,
    }


@router.put("/{image_id}")
def update_gallery_image(
    image_id: str,
    body: UpdateDescriptionRequest,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    img = session.get(GalleryImage, image_id)
    if not img:
        raise HTTPException(status_code=404)
    img.description = body.description.strip()
    session.add(img)
    session.commit()
    session.refresh(img)
    return {"id": img.id, "description": img.description}


@router.delete("/{image_id}", status_code=204)
def delete_gallery_image(
    image_id: str,
    current_user=Depends(require_role("admin", "teacher")),
    session: Session = Depends(get_session),
):
    img = session.get(GalleryImage, image_id)
    if not img:
        raise HTTPException(status_code=404)
    session.delete(img)
    session.commit()
