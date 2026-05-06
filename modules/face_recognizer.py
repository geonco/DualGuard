"""FaceNet 기반 얼굴 인식 + DB 매칭 (Stage 1).

facenet-pytorch의 InceptionResNetV1으로 얼굴 영역에서 512차원 임베딩을 추출하고,
등록 DB(embeddings.npy)와 코사인 유사도로 비교하여 사용자명 또는 ``Unknown``을
반환한다.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


class FaceRecognizer:
    """FaceNet 임베딩 추출기 + DB 매처."""

    def __init__(self, threshold: float = 0.7, device: str = "cpu") -> None:
        """모델 로드 및 임계값 설정.

        TODO:
            - facenet_pytorch.InceptionResNetV1(pretrained='vggface2') 로드
            - eval(), .to(device)
            - DataManager로부터 users / embeddings 캐시 받기
        """
        raise NotImplementedError

    def embed(self, face_bgr: np.ndarray) -> np.ndarray:
        """얼굴 이미지 → 512-d L2 정규화 임베딩.

        TODO:
            - 160x160 리사이즈, BGR→RGB, 텐서 정규화
            - 추론 후 numpy 변환 + L2 normalize
        """
        raise NotImplementedError

    def match(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """등록 DB와 코사인 유사도 비교.

        Returns:
            (이름 or None, 최고 유사도). 임계값 미만이면 (None, score).

        TODO:
            - DB embeddings (N, 512)와 dot product
            - argmax 후 임계값 체크
        """
        raise NotImplementedError

    def reload_database(self) -> None:
        """등록 후 DB 재로딩. TODO."""
        raise NotImplementedError
