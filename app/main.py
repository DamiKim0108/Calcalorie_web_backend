# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from . import db_models  # noqa: F401 (테이블 생성 위해 import)
from .routers import post_router, user_router

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CommunityProject API")

# CORS 설정 (프론트엔드 주소에 맞춰 수정)
origins = [
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 (기본 이미지 등) 서빙
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 라우터 등록
app.include_router(user_router.router)
app.include_router(post_router.router)

