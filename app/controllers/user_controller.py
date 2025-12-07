# backend/app/controllers/user_controller.py
from typing import Dict, Any

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db_models import User
from ..schemas import user_schema
from fastapi.encoders import jsonable_encoder
#from app.core.security import hash_password 


def signup_controller(db: Session, payload: Dict[str, Any]):
    try:
        data = user_schema.UserCreate(**payload)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"message": "invalid_request", "data": None},
        )

    # 이메일 중복 확인
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        return JSONResponse(
            status_code=409,
            content={"message": "email_already_exists", "data": None},
        )

    user = User(
        email=data.email,
        password=data.password,  
        nickname=data.nickname,
        profile_image=data.profile_image,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user_out = user_schema.UserOut.from_orm(user)

    return JSONResponse(
        status_code=201,
        content=jsonable_encoder(
            {
                "message": "register_success",
                "data": user_out,
            }
        ),
    )


def login_controller(db: Session, payload: Dict[str, Any]):
    print("🔥🔥🔥 PAYLOAD RECEIVED:", payload)
    print("type:", type(payload))

    # 1) payload 기본 구조 체크 (email, password 키 존재 여부)
    if "email" not in payload or "password" not in payload:
        return JSONResponse(
            status_code=400,
            content={"message": "invalid_request", "data": None},
        )

    # 2) Pydantic 검증 (형식 검증)
    try:
        data = user_schema.UserLogin(**payload)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"message": "invalid_request", "data": None},
        )

    # 3) 회원 조회
    user = db.query(User).filter(User.email == data.email).first()

    # 3-1) 회원 없음
    if not user:
        return JSONResponse(
            status_code=404,
            content={"message": "user_not_found", "data": None},
        )

    # 4) 비밀번호 틀림
    if user.password != data.password:
        return JSONResponse(
            status_code=401,
            content={"message": "unauthorized", "data": None},
        )

    # ✅ 5) 로그인 성공 - user_id 포함해서 반환!
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(
            {
                "message": "login_success",
                "data": {
                    "user_id": user.id,  # 🔥 이게 핵심!
                    "email": user.email,
                    "nickname": user.nickname,
                    "profile_image": user.profile_image,
                },
            }
        ),
    )


def update_user_controller(db: Session, user_id: int, payload: Dict[str, Any]):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"message": "user_not_found", "data": None},
        )

    # 닉네임만 꺼내서 별도 검증
    nickname = (payload.get("nickname") or "").strip()

    if not nickname:
        return JSONResponse(
            status_code=400,
            content={"message": "nickname_required", "data": None},
        )

    if len(nickname) > 10:
        return JSONResponse(
            status_code=400,
            content={"message": "nickname_too_long", "data": None},
        )

    # 중복 체크 (본인 제외)
    dup = (
        db.query(User)
        .filter(User.nickname == nickname, User.id != user_id)
        .first()
    )
    if dup:
        return JSONResponse(
            status_code=409,
            content={"message": "nickname_duplicated", "data": None},
        )

    # 실제 업데이트
    user.nickname = nickname

    profile_image = payload.get("profile_image", None)
    if profile_image is not None:
        user.profile_image = profile_image

    db.commit()
    db.refresh(user)

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(
            {
                "message": "update_success",
                "data": user_schema.UserOut.from_orm(user),
            }
        ),
    )



def delete_user_controller(db: Session, user_id: int):
    """
    회원 탈퇴 컨트롤러 (유저 + cascade 걸린 게시글/댓글 삭제)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"message": "user_not_found", "data": None},
        )

    db.delete(user)
    db.commit()
    return JSONResponse(
        status_code=204,
        content={"message": "delete_success", "data": None},
    )

def update_password_controller(db: Session, user_id: int, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # 비밀번호 해시 후 저장
    user.password = new_password
    db.commit()
    db.refresh(user)

    return {"message": "password updated"}