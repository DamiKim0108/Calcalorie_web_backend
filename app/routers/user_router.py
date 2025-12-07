# backend/app/routers/user_router.py
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..controllers import user_controller
from app.schemas.user_schema import UserPasswordUpdate


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup")
def signup(payload: Dict[str, Any], db: Session = Depends(get_db)):
    return user_controller.signup_controller(db, payload)


@router.post("/login")
def login(payload: Dict[str, Any], db: Session = Depends(get_db)):
    return user_controller.login_controller(db, payload)

# ✅ 회원정보 수정
@router.patch("/{user_id}")
def update_user(user_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    return user_controller.update_user_controller(db, user_id, payload)


# ✅ 회원 탈퇴
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return user_controller.delete_user_controller(db, user_id)


@router.put("/{user_id}/password")
def update_password(user_id: int, req: UserPasswordUpdate, db: Session = Depends(get_db)):
    return user_controller.update_password_controller(db, user_id, req.new_password)