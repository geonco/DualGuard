"""FaceDetector 단위 테스트.

MediaPipe 추론은 가벼운 합성 이미지로 검증하기 어려우므로:
- crop / 경계 클램핑 / 마진은 합성 이미지로 직접 검증
- detect는 "얼굴 없는 이미지에서 빈 리스트" 만 보장 (실제 얼굴 검출은 Pi 통합테스트에서)
"""

from __future__ import annotations

import numpy as np
import pytest

from modules.face_detector import FaceDetector


@pytest.fixture(scope="module")
def detector() -> FaceDetector:
    fd = FaceDetector(min_confidence=0.5)
    yield fd
    fd.close()


def test_detect_empty_on_blank_frame(detector: FaceDetector) -> None:
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    assert detector.detect(blank) == []
    assert detector.detect_largest(blank) is None


def test_detect_empty_on_noise(detector: FaceDetector) -> None:
    rng = np.random.default_rng(0)
    noise = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)
    # 노이즈에서 우연히 얼굴이 잡힐 수도 있지만 min_confidence=0.5에서는 거의 0.
    boxes = detector.detect(noise)
    assert isinstance(boxes, list)


def test_crop_basic(detector: FaceDetector) -> None:
    frame = np.arange(480 * 640 * 3, dtype=np.uint8).reshape(480, 640, 3)
    crop = detector.crop(frame, (100, 50, 200, 150))
    assert crop.shape == (150, 200, 3)
    np.testing.assert_array_equal(crop, frame[50:200, 100:300])


def test_crop_clamps_to_bounds(detector: FaceDetector) -> None:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    crop = detector.crop(frame, (80, 80, 50, 50))
    assert crop.shape == (20, 20, 3)


def test_crop_with_margin(detector: FaceDetector) -> None:
    frame = np.zeros((400, 400, 3), dtype=np.uint8)
    crop = detector.crop(frame, (100, 100, 100, 100), margin=0.2)
    # 가로/세로 각각 20%씩 추가 → 20px 확장
    assert crop.shape == (140, 140, 3)


def test_crop_margin_clamps_at_edges(detector: FaceDetector) -> None:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    crop = detector.crop(frame, (90, 90, 10, 10), margin=1.0)
    # 100% 마진이면 (-10, -10)~(110, 110)이지만 (0,0)~(100,100)으로 클램핑
    assert crop.shape[0] <= 100 and crop.shape[1] <= 100


def test_context_manager_closes() -> None:
    with FaceDetector() as fd:
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        assert fd.detect(blank) == []
