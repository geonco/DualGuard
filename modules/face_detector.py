"""MediaPipe Face Detection 래퍼 (Stage 0).

영상 프레임에서 얼굴 영역(Bounding Box)을 추출하여 후속 인식/위조검증
스테이지에 전달한다.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


BBox = Tuple[int, int, int, int]  # (x, y, w, h)


class FaceDetector:
    """MediaPipe Face Detection 기반 얼굴 검출기."""

    def __init__(self, min_confidence: float = 0.5) -> None:
        """검출기 초기화.

        TODO:
            - mediapipe.solutions.face_detection.FaceDetection 인스턴스 생성
            - min_detection_confidence=min_confidence
        """
        raise NotImplementedError

    def detect(self, frame_bgr: np.ndarray) -> List[BBox]:
        """프레임에서 얼굴 박스 리스트를 반환.

        Args:
            frame_bgr: OpenCV BGR 이미지.

        Returns:
            (x, y, w, h) 좌표 튜플 리스트. 얼굴이 없으면 빈 리스트.

        TODO:
            - BGR → RGB 변환
            - MediaPipe 추론
            - 정규화 좌표 → 픽셀 좌표 변환
        """
        raise NotImplementedError

    def crop(self, frame_bgr: np.ndarray, bbox: BBox) -> np.ndarray:
        """bbox 영역만 잘라서 반환. 경계 밖이면 클램핑.

        TODO: numpy 슬라이싱 + 경계 검사.
        """
        raise NotImplementedError

    def close(self) -> None:
        """리소스 해제. TODO."""
        raise NotImplementedError
