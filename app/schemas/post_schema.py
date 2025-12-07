# backend/app/schemas/post_schema.py
from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, Field

MAX_TITLE_LEN = 26

# 사진이 없을 때 목록에 보여줄 기본 썸네일
DEFAULT_POST_THUMBNAIL_URL = "/static/default_img.jpg"


# ---------- 요청용 ---------- #
class PostCreate(BaseModel):
    author_id: int
    title: str = Field(min_length=1, max_length=MAX_TITLE_LEN)
    body: str = Field(min_length=1)
    image_url: Optional[str] = None


class CommentCreate(BaseModel):
    author_id: int
    content: str = Field(min_length=1, max_length=500)


# ---------- 응답용: 목록 ---------- #
class PostListItem(BaseModel):
    id: int
    title: str
    created_at: str
    comments: str
    views: str
    detail_url: str
    thumbnail_url: str
    colors: Dict[str, str]


# ---------- 응답용: 상세 ---------- #
class CommentOut(BaseModel):
    id: int
    author: str
    content: str
    created_at: str


class PostDetail(BaseModel):
    id: int
    title: str
    body: str
    author: str
    created_at: str
    views: int
    views_display: str
    comments_count: int
    comments_count_display: str
    likes: int
    image_url: Optional[str] = None
    comments: List[CommentOut]


# ---------- 헬퍼 ---------- #
def _compact_count(num: Optional[int]) -> str:
    """숫자를 1.2K 같이 줄여서 표시. None이면 0 처리."""
    if num is None:
        return "0"
    if num >= 10000:
        return f"{num // 1000}K"
    if num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)


def _format_dt(dt: Optional[datetime]) -> str:
    """datetime이 None이어도 안전하게 문자열로 변환."""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def make_list_item(post, comments_count: int) -> PostListItem:
    # 제목 자르기
    title = post.title or ""
    if len(title) > MAX_TITLE_LEN:
        title = title[:MAX_TITLE_LEN]

    # 썸네일 처리 (image_url 없으면 기본 썸네일)
    thumbnail = getattr(post, "image_url", None) or DEFAULT_POST_THUMBNAIL_URL

    created_at_str = _format_dt(getattr(post, "created_at", None))
    views_val = getattr(post, "views", 0) or 0

    return PostListItem(
        id=post.id,
        title=title,
        created_at=created_at_str,
        comments=_compact_count(comments_count),
        views=_compact_count(views_val),
        detail_url=f"/posts/{post.id}",
        thumbnail_url=thumbnail,
        colors={"default": "#ACA0EB", "hover": "#7F6AEE"},
    )


def make_detail(post, comments: List[CommentOut]) -> PostDetail:
    comments_count = len(comments)

    created_at_str = _format_dt(getattr(post, "created_at", None))
    views_val = getattr(post, "views", 0) or 0

    author_nickname = "unknown"
    author = getattr(post, "author", None)
    if author is not None and getattr(author, "nickname", None):
        author_nickname = author.nickname

    return PostDetail(
        id=post.id,
        title=post.title or "",
        body=post.body or "",
        author=author_nickname,
        created_at=created_at_str,
        views=views_val,
        views_display=_compact_count(views_val),
        comments_count=comments_count,
        comments_count_display=_compact_count(comments_count),
        likes=0,  # 아직 좋아요 기능 없음
        image_url=getattr(post, "image_url", None),
        comments=comments,
    )
