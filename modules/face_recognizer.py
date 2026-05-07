"""FaceNet 기반 얼굴 인식 + DB 매칭 (Stage 1).

facenet-pytorch의 InceptionResNetV1(VGGFace2 사전학습)으로 얼굴 영역에서
512차원 임베딩을 추출하고, 등록 DB(embeddings.npy)와 코사인 유사도로 비교하여
사용자명 또는 ``Unknown``을 반환한다.

임베딩은 모두 L2 정규화된 단위 벡터이므로 코사인 유사도 = 내적이다.
"""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1

import config
from modules.data_manager import DataManager, EMBEDDING_DIM

FACENET_INPUT_SIZE = 160


class FaceRecognizer:
    """FaceNet 임베딩 추출기 + DB 매처."""

    def __init__(
        self,
        threshold: float | None = None,
        device: str = "cpu",
        data_manager: DataManager | None = None,
    ) -> None:
        self.threshold = threshold if threshold is not None else config.FACENET_SIM_THRESHOLD
        self.device = torch.device(device)

        self._model = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)

        self._dm = data_manager or DataManager()
        self._names: list[str] = []
        self._db: np.ndarray = np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
        self.reload_database()

    def reload_database(self) -> None:
        """register.py 가 새 사용자 추가 후 호출하면 in-memory DB가 갱신된다."""
        names, embs = self._dm.get_users_and_embeddings()
        self._names = names
        if embs.shape[0] == 0:
            self._db = np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
            return
        self._db = self._l2_normalize(embs.astype(np.float32))

    @staticmethod
    def _l2_normalize(x: np.ndarray, eps: float = 1e-10) -> np.ndarray:
        norm = np.linalg.norm(x, axis=-1, keepdims=True)
        return x / np.maximum(norm, eps)

    def embed(self, face_bgr: np.ndarray) -> np.ndarray:
        """얼굴 crop → 512-d L2 정규화 임베딩."""
        if face_bgr.size == 0:
            raise ValueError("empty face image")

        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (FACENET_INPUT_SIZE, FACENET_INPUT_SIZE))

        # facenet-pytorch 권장 정규화: (x - 127.5) / 128.0
        tensor = torch.from_numpy(resized).float().permute(2, 0, 1)
        tensor = (tensor - 127.5) / 128.0
        tensor = tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self._model(tensor).cpu().numpy()[0]
        return self._l2_normalize(emb).astype(np.float32)

    def match(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """DB와 코사인 유사도 → (이름 또는 None, 최고 점수).

        DB가 비어있으면 (None, 0.0).
        """
        if self._db.shape[0] == 0:
            return None, 0.0

        sims = self._db @ embedding  # (N,) 코사인 유사도 (둘 다 L2 정규화)
        idx = int(np.argmax(sims))
        score = float(sims[idx])

        if score >= self.threshold:
            return self._names[idx], score
        return None, score

    def identify(self, face_bgr: np.ndarray) -> Tuple[Optional[str], float, np.ndarray]:
        """embed + match 한 번에. 임베딩도 같이 반환 (등록 시 재사용 위해)."""
        emb = self.embed(face_bgr)
        name, score = self.match(emb)
        return name, score, emb
