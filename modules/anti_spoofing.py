"""MiniFASNet 기반 Anti-Spoofing (Stage 2).

Silent-Face-Anti-Spoofing(MiniFASNet) 모델로 얼굴 영역의 Real/Spoof 여부를
분류한다. 사진/영상/마스크 등 위조 시도 차단이 핵심 책임.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


class AntiSpoofing:
    """MiniFASNet Real/Spoof 분류기."""

    def __init__(self, weights_path: str, threshold: float = 0.5,
                 device: str = "cpu") -> None:
        """모델 로드.

        TODO:
            - MiniFASNet 아키텍처 정의 import 후 weights_path 로드
            - eval(), .to(device)
        """
        raise NotImplementedError

    def predict(self, face_bgr: np.ndarray) -> Tuple[bool, float]:
        """Real/Spoof 분류.

        Returns:
            (is_real, real_confidence). real_confidence가 임계값 이상이면 True.

        TODO:
            - 입력 전처리 (스케일/크롭은 모델 명세에 맞춤)
            - softmax 후 Real 클래스 확률 추출
        """
        raise NotImplementedError
