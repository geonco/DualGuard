"""MediaPipe Face Detection 래퍼 (Stage 0).

영상 프레임에서 얼굴 영역(Bounding Box)을 추출하여 후속 인식/위조검증
스테이지에 전달한다. 얼굴이 없으면 빈 리스트를 반환하므로 main 루프는
즉시 다음 프레임으로 넘어갈 수 있다.
"""

from __future__ import annotations

from typing import List, Tuple

import cv2
import mediapipe as mp
import numpy as np

BBox = Tuple[int, int, int, int]  # (x, y, w, h)


class FaceDetector:
    """MediaPipe Face Detection 기반 얼굴 검출기."""

    def __init__(self, min_confidence: float = 0.5, model_selection: int = 0) -> None:
        """
        Args:
            min_confidence: 검출 최소 신뢰도.
            model_selection: 0=근거리(2m 이내), 1=원거리(최대 5m). 출입 시나리오는 0.
        """
        self._detector = mp.solutions.face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_confidence,
        )

    def detect(self, frame_bgr: np.ndarray) -> List[BBox]:
        """프레임에서 얼굴 박스 리스트를 반환. 얼굴이 없으면 빈 리스트."""
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self._detector.process(rgb)

        if not result.detections:
            return []

        boxes: List[BBox] = []
        for det in result.detections:
            rel = det.location_data.relative_bounding_box
            x = int(rel.xmin * w)
            y = int(rel.ymin * h)
            bw = int(rel.width * w)
            bh = int(rel.height * h)
            x, y = max(0, x), max(0, y)
            bw = min(bw, w - x)
            bh = min(bh, h - y)
            if bw > 0 and bh > 0:
                boxes.append((x, y, bw, bh))
        return boxes

    def detect_largest(self, frame_bgr: np.ndarray) -> BBox | None:
        """면적이 가장 큰 얼굴 하나만 반환. 출입 시나리오에서는 보통 한 명만 다룸."""
        boxes = self.detect(frame_bgr)
        if not boxes:
            return None
        return max(boxes, key=lambda b: b[2] * b[3])

    def crop(self, frame_bgr: np.ndarray, bbox: BBox, margin: float = 0.0) -> np.ndarray:
        """bbox 영역을 잘라서 반환. 경계 밖이면 클램핑.

        Args:
            margin: bbox 가로/세로 대비 추가 여유 비율 (0.2 = 20% 확장).
                FaceNet/MiniFASNet에 더 넉넉한 컨텍스트를 주고 싶을 때 사용.
        """
        h, w = frame_bgr.shape[:2]
        x, y, bw, bh = bbox
        if margin > 0:
            mx, my = int(bw * margin), int(bh * margin)
            x -= mx
            y -= my
            bw += 2 * mx
            bh += 2 * my
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(w, x + bw)
        y1 = min(h, y + bh)
        return frame_bgr[y0:y1, x0:x1].copy()

    def close(self) -> None:
        self._detector.close()

    def __enter__(self) -> "FaceDetector":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
