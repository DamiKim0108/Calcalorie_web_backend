# schemas/ai_model.py

from __future__ import annotations
from transformers import pipeline

MODEL_NAME = "jinkyeongk/kcELECTRA-toxic-detector"

# 전역 파이프라인 로딩
try:
    toxic_clf = pipeline(
        "text-classification",
        model=MODEL_NAME,
        # top_k=1  # 기본값이라 생략 가능
    )
    _AI_MODEL_AVAILABLE = True
except Exception as e:
    # 모델 로딩 실패 시, 플래그만 False로 두고 나중에 처리
    toxic_clf = None
    _AI_MODEL_AVAILABLE = False
    _AI_MODEL_LOAD_ERROR = str(e)


def check_toxic(text: str, threshold: float = 0.5) -> dict:
    """
    문장을 넣으면 혐오 여부 + 에러 여부까지 리턴.
    반환 형식:
    {
      "success": bool,       # AI 추론 성공 여부
      "error": str | None,   # 에러 메시지(있다면)
      "is_toxic": bool,      # 혐오로 판단했는지
      "label": str,          # 모델이 낸 label (LABEL_0 / LABEL_1 등)
      "score": float         # 해당 label의 score
    }
    """
    # 1) 모델이 아예 로딩되지 않은 경우
    if not _AI_MODEL_AVAILABLE or toxic_clf is None:
        return {
            "success": False,
            "error": _AI_MODEL_LOAD_ERROR if '_AI_MODEL_LOAD_ERROR' in globals() else "model_not_available",
            "is_toxic": False,
            "label": "AI_ERROR",
            "score": 0.0,
        }

    if not text or not text.strip():
        return {
            "success": True,
            "error": None,
            "is_toxic": False,
            "label": "EMPTY",
            "score": 0.0,
        }

    try:
        result = toxic_clf(text)[0]   # [{'label': 'LABEL_x', 'score': ...}]
        label = result["label"]
        score = float(result["score"])

        is_toxic = (label == "LABEL_1") and (score >= threshold)

        return {
            "success": True,
            "error": None,
            "is_toxic": is_toxic,
            "label": label,
            "score": score,
        }

    except Exception as e:
        # 추론 중 에러 (메모리 부족, 토치 내부 에러 등)
        return {
            "success": False,
            "error": str(e),
            "is_toxic": False,
            "label": "AI_ERROR",
            "score": 0.0,
        }
