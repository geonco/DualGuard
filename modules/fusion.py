"""융합 알고리즘 (명세서 F5).

두 모델의 결과를 결합하여 최종 Pass/Reject를 결정한다.

- 방식 A: 단순 AND (FaceNet ≥ τ1 AND MiniFASNet ≥ τ2)
- 방식 B: 가중 융합 (α·face + β·fas ≥ τ_combined)

두 방식을 동일 데이터셋으로 평가해 보고서에 비교 결과 표를 싣는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FusionResult:
    """최종 결정 결과."""
    passed: bool
    reason: str           # "OK" | "UnknownUser" | "SpoofDetected"
    user: Optional[str]
    facenet_score: float
    fasnet_score: float


def decide_and(user: Optional[str], facenet_score: float,
               fasnet_score: float, face_threshold: float,
               fas_threshold: float) -> FusionResult:
    """방식 A: AND 결합. TODO."""
    raise NotImplementedError


def decide_weighted(user: Optional[str], facenet_score: float,
                    fasnet_score: float, alpha: float, beta: float,
                    combined_threshold: float) -> FusionResult:
    """방식 B: 가중 융합. TODO.

    final = α·facenet_score + β·fasnet_score
    user가 None이면 UnknownUser로 즉시 reject.
    """
    raise NotImplementedError
