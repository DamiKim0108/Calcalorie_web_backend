# backend/app/routers/post_router.py
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
import shutil

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..controllers import post_controller

router = APIRouter(prefix="/posts", tags=["posts"])

UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("")
def list_posts(cursor: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return post_controller.list_posts_controller(db, cursor, limit)


@router.get("/{post_id}")
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    return post_controller.get_post_detail_controller(db, post_id)


@router.post("")
async def create_post(
    title: str = Form(...),
    body: str = Form(...),
    user_id: int = Form(...),
    image: Optional[UploadFile] = File(None),  # ✅ 파일은 UploadFile 로 받기
    db: Session = Depends(get_db),
):
    image_url: Optional[str] = None

    if image is not None:
        # 확장자 추출 (png, jpg 등)
        ext = image.filename.rsplit(".", 1)[-1].lower()
        # 중복 방지 UUID 파일명
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = UPLOAD_DIR / filename

        # 실제 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # 브라우저에서 접근 가능한 URL
        image_url = f"/static/uploads/{filename}"

    payload: Dict[str, Any] = {
        "title": title,
        "body": body,
        "author_id": user_id,
        "image_url": image_url,  # ✅ DB에 저장할 이미지 URL
    }

    return post_controller.create_post_controller(db, payload)

@router.post("/{post_id}/comments")
def create_comment(
    post_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    return post_controller.create_comment_controller(db, post_id, payload)
