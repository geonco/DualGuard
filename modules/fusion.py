"""융합 알고리즘 (명세서 F5).

두 모델의 결과를 결합하여 최종 Pass/Reject를 결정한다.

- 방식 A: 단순 AND (FaceNet ≥ τ1 AND MiniFASNet ≥ τ2)
- 방식 B: 가중 융합 (α·face + β·fas ≥ τ_combined)

둘 다 동일 인터페이스(FusionResult)로 결과를 반환해 보고서 표 1 비교 평가가
가능하다. user가 None(미등록자)이면 두 방식 모두 즉시 UnknownUser로 reject.

명세서 우선순위: UnknownUser > SpoofDetected (Stage 1에서 먼저 실패한 사유 채택).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

REASON_OK = "OK"
REASON_UNKNOWN = "UnknownUser"
REASON_SPOOF = "SpoofDetected"


@dataclass
class FusionResult:
    """최종 결정 결과."""
    passed: bool
    reason: str
    user: Optional[str]
    facenet_score: float
    fasnet_score: float


def decide_and(
    user: Optional[str],
    facenet_score: float,
    fasnet_score: float,
    face_threshold: float,
    fas_threshold: float,
) -> FusionResult:
    """방식 A: 단순 AND 결합 (베이스라인).

    조건: facenet_score ≥ face_threshold AND fasnet_score ≥ fas_threshold.
    """
    if user is None:
        return FusionResult(False, REASON_UNKNOWN, None, facenet_score, fasnet_score)

    face_ok = facenet_score >= face_threshold
    fas_ok = fasnet_score >= fas_threshold

    if face_ok and fas_ok:
        return FusionResult(True, REASON_OK, user, facenet_score, fasnet_score)

    # face_ok=False는 user is None과 의미가 충돌 — 호출 측에서 user를 None으로
    # 넘겨야 했지만 일관성 위해 UnknownUser로 처리.
    if not face_ok:
        return FusionResult(False, REASON_UNKNOWN, user, facenet_score, fasnet_score)
    return FusionResult(False, REASON_SPOOF, user, facenet_score, fasnet_score)


def decide_weighted(
    user: Optional[str],
    facenet_score: float,
    fasnet_score: float,
    alpha: float,
    beta: float,
    combined_threshold: float,
) -> FusionResult:
    """방식 B: 가중 융합.

    final = α·facenet_score + β·fasnet_score, final ≥ combined_threshold 이면 통과.
    α + β = 1 가정 (호출 측 책임). user가 None이면 UnknownUser 즉시 reject.

    실패 사유는 두 점수 중 더 낮은 쪽 기준 — 명세서 9.3 표 1 비교를 위해
    "어느 모델이 막았는지" 추적할 수 있게 함.
    """
    if user is None:
        return FusionResult(False, REASON_UNKNOWN, None, facenet_score, fasnet_score)

    final = alpha * facenet_score + beta * fasnet_score
    if final >= combined_threshold:
        return FusionResult(True, REASON_OK, user, facenet_score, fasnet_score)

    # 둘 중 더 낮은 점수 쪽이 차단 사유
    if facenet_score < fasnet_score:
        return FusionResult(False, REASON_UNKNOWN, user, facenet_score, fasnet_score)
    return FusionResult(False, REASON_SPOOF, user, facenet_score, fasnet_score)
