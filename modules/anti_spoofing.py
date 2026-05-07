"""MiniFASNet 기반 Anti-Spoofing (Stage 2).

Silent-Face-Anti-Spoofing 저장소(외부 의존성)의 MiniFASNetV1SE / MiniFASNetV2
두 모델을 앙상블하여 Real / Spoof 확률을 계산한다.

저장소 위치는 ``config.SILENT_FACE_ROOT`` 로 지정한다 (기본 ~/Silent-Face-Anti-Spoofing).
모델 정의 + 가중치(.pth) 모두 그 저장소에서 사용 — 우리 ``models/`` 디렉토리에
복사하지 않는다.

추론 출력은 3-class 확률 (index 1 = Real). 두 모델 평균을 취해 ``real_prob`` 반환.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from typing import Tuple

import numpy as np

import config

BBox = Tuple[int, int, int, int]  # (x, y, w, h)


def _ensure_silent_face_on_path() -> None:
    root = str(config.SILENT_FACE_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


@contextlib.contextmanager
def _chdir(path: Path):
    """일시적으로 CWD 변경 — Silent-Face가 상대경로로 자체 검출기 가중치를 로드하는
    문제 우회용.
    """
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


class AntiSpoofing:
    """MiniFASNet 앙상블 위조 검증기."""

    def __init__(self, threshold: float | None = None, device_id: int = 0) -> None:
        """
        Args:
            threshold: Real 확률 임계값. 기본값은 ``config.FASNET_REAL_THRESHOLD``.
            device_id: CUDA device id. Pi엔 GPU 없으니 사실상 무시되고 CPU로 떨어진다.
        """
        self.threshold = (
            threshold if threshold is not None else config.FASNET_REAL_THRESHOLD
        )

        _ensure_silent_face_on_path()
        # Silent-Face 저장소의 src 모듈 — sys.path 주입 후에야 import 가능.
        from src.anti_spoof_predict import AntiSpoofPredict
        from src.generate_patches import CropImage
        from src.utility import parse_model_name

        self._parse_model_name = parse_model_name
        self._cropper = CropImage()
        # AntiSpoofPredict 부모(Detection)가 상대경로로 Caffe 모델을 로드하므로
        # 그 디렉토리에서 init만 실행시킨 후 복귀.
        with _chdir(config.SILENT_FACE_ROOT):
            self._predictor = AntiSpoofPredict(device_id)

        if not config.MINIFASNET_WEIGHTS_DIR.exists():
            raise FileNotFoundError(
                f"MiniFASNet weights dir not found: {config.MINIFASNET_WEIGHTS_DIR}\n"
                f"Clone Silent-Face-Anti-Spoofing under {config.SILENT_FACE_ROOT}."
            )
        self._model_paths = sorted(config.MINIFASNET_WEIGHTS_DIR.glob("*.pth"))
        if not self._model_paths:
            raise FileNotFoundError(
                f"No .pth files in {config.MINIFASNET_WEIGHTS_DIR}"
            )

    def predict_real_score(self, frame_bgr: np.ndarray, bbox: BBox) -> float:
        """프레임 + 얼굴 bbox → Real 확률 (0~1).

        두 모델의 3-class 확률을 평균하고 index 1(Real)을 반환.
        """
        x, y, w, h = bbox
        face_box = [int(x), int(y), int(w), int(h)]

        accum = np.zeros((1, 3), dtype=np.float64)
        for mp in self._model_paths:
            h_in, w_in, _model_type, scale = self._parse_model_name(mp.name)
            crop_args = {
                "org_img": frame_bgr,
                "bbox": face_box,
                "scale": scale,
                "out_w": w_in,
                "out_h": h_in,
                "crop": True,
            }
            if scale is None:
                crop_args["crop"] = False
            patch = self._cropper.crop(**crop_args)
            accum += self._predictor.predict(patch, str(mp))

        accum /= len(self._model_paths)
        return float(accum[0][1])

    def is_real(self, real_score: float) -> bool:
        return real_score >= self.threshold

    def predict(self, frame_bgr: np.ndarray, bbox: BBox) -> Tuple[bool, float]:
        """편의 메서드 — (is_real, real_score) 반환."""
        score = self.predict_real_score(frame_bgr, bbox)
        return self.is_real(score), score
