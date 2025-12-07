# backend/app/controllers/post_controller.py
from typing import Dict, Any

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db_models import Post, Comment, User
from ..schemas import post_schema
from ..AI.ai_model import check_toxic


# ---------- 목록 ---------- #
def list_posts_controller(db: Session, cursor: int, limit: int):
    try:
        total = db.query(Post).count()

        posts = (
            db.query(Post)
            .order_by(Post.id.asc())
            .offset(cursor)
            .limit(limit)
            .all()
        )

        items = []
        for p in posts:
            comments_count = (
                db.query(Comment)
                .filter(Comment.post_id == p.id)
                .count()
            )
            items.append(post_schema.make_list_item(p, comments_count))

        return JSONResponse(
            status_code=200,
            content={
                "message": "list_ok",
                "data": {
                    "total": total,
                    "cursor": cursor,
                    "limit": limit,
                    "posts": [i.dict() for i in items],
                },
            },
        )
    except Exception as e:
        import traceback

        print("[list_posts_controller] ERROR")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"message": "internal_server_error", "data": None},
        )


# ---------- 상세 ---------- #
def get_post_detail_controller(db: Session, post_id: int):
    try:
        # 1) 게시글 찾기
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return JSONResponse(
                status_code=404,
                content={"message": "post_not_found", "data": None},
            )

        # 2) views가 None인 예전 데이터 방어
        if post.views is None:
            post.views = 0

        # 3) 조회수 +1
        post.views += 1
        db.commit()
        db.refresh(post)

        # 4) 댓글 목록 조회
        comments = (
            db.query(Comment)
            .filter(Comment.post_id == post.id)
            .order_by(Comment.created_at.asc())
            .all()
        )

        # 5) 댓글 스키마로 변환
        comments_out = []
        for c in comments:
            try:
                # author 정보 안전하게 추출
                author_nickname = "unknown"
                if hasattr(c, 'author') and c.author:
                    author_nickname = getattr(c.author, 'nickname', 'unknown')
                elif hasattr(c, 'author_id') and c.author_id:
                    # author 관계가 없으면 DB에서 직접 조회
                    author = db.query(User).filter(User.id == c.author_id).first()
                    if author:
                        author_nickname = author.nickname

                # created_at 안전하게 처리
                created_at_str = ""
                if hasattr(c, 'created_at') and c.created_at:
                    created_at_str = c.created_at.strftime("%Y-%m-%d %H:%M:%S")

                comment_out = post_schema.CommentOut(
                    id=c.id,
                    author=author_nickname,
                    content=c.content,
                    created_at=created_at_str,
                )
                comments_out.append(comment_out)
            except Exception as comment_error:
                print(f"[Warning] 댓글 변환 오류 (comment_id={c.id}):", repr(comment_error))
                # 오류난 댓글은 건너뛰기
                continue

        # 6) 상세 스키마 생성
        detail = post_schema.make_detail(post, comments_out)

        return JSONResponse(
            status_code=200,
            content={"message": "detail_ok", "data": detail.dict()},
        )

    except Exception as e:
        import traceback
        print("[get_post_detail_controller] ERROR")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"message": "internal_server_error", "data": None},
        )


# ---------- 글 작성 ---------- #
# ---------- 글 작성 ---------- #
def create_post_controller(db: Session, payload: Dict[str, Any]):
    try:
        data = post_schema.PostCreate(**payload)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"message": "invalid_request", "data": None},
        )

    # 작성자 확인
    user = db.query(User).filter(User.id == data.author_id).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"message": "user_not_found", "data": None},
        )

    # AI 비도덕성 검사
    moderation = check_toxic(f"{data.title}\n{data.body}", threshold=0.7)
    if not moderation["success"]:
        return JSONResponse(
            status_code=500,
            content={
                "message": "ai_error",
                "data": {"detail": moderation.get("error")},
            },
        )
    if moderation["is_toxic"]:
        return JSONResponse(
            status_code=403,
            content={
                "message": "blocked_toxic_post",
                "data": {
                    "model_label": moderation.get("label"),
                    "score": moderation.get("score"),
                },
            },
        )

    # 실제 Post 생성
    post = Post(
        title=data.title.strip(),
        body=data.body.strip(),
        author_id=data.author_id,
        image_url=(data.image_url.strip() if data.image_url else None),
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # ✅ 여기 응답 구조가 프론트에서 postId 뽑는 기준
    return JSONResponse(
        status_code=201,
        content={
            "message": "post_created",
            "data": {
                "post_id": post.id,                 # ← 핵심!
                "id": post.id,                      # ← 혹시 몰라서 같이 넣어줌
                "detail_url": f"/posts/{post.id}",
            },
        },
    )



# ---------- 댓글 작성 ---------- #
def create_comment_controller(db: Session, post_id: int, payload: Dict[str, Any]):
    try:
        data = post_schema.CommentCreate(**payload)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"message": "invalid_request", "data": None},
        )

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return JSONResponse(
            status_code=404,
            content={"message": "post_not_found", "data": None},
        )

    user = db.query(User).filter(User.id == data.author_id).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"message": "user_not_found", "data": None},
        )

    # 여기서는 댓글에 대한 비도덕성 검사는 생략 (원하면 check_toxic 추가 가능)
    comment = Comment(
        post_id=post.id,
        author_id=user.id,
        content=data.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return JSONResponse(
        status_code=201,
        content={
            "message": "comment_created",
            "data": {
                "id": comment.id,
                "post_id": post.id,
            },
        },
    )