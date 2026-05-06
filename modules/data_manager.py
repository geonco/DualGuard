"""데이터 영속성 관리 (명세서 4.3, F6).

users.json, embeddings.npy, access_log.csv의 입출력을 캡슐화한다.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


class DataManager:
    """JSON / numpy / CSV 통합 데이터 레이어."""

    def __init__(self) -> None:
        """경로 검증 및 lazy-load 준비.

        TODO:
            - config의 USERS_JSON / EMBEDDINGS_NPY / ACCESS_LOG_CSV 경로 보관
            - data 디렉토리 미존재 시 생성
            - access_log.csv 헤더 보장
        """
        raise NotImplementedError

    # ---- 사용자 ----------------------------------------------------------
    def load_users(self) -> Dict[str, dict]:
        """users.json 로드. 없으면 빈 dict. TODO."""
        raise NotImplementedError

    def load_embeddings(self) -> np.ndarray:
        """embeddings.npy 로드. 없으면 (0, 512) 빈 배열. TODO."""
        raise NotImplementedError

    def add_user(self, name: str, mean_embedding: np.ndarray) -> int:
        """신규 사용자 추가 후 embedding_index 반환.

        TODO:
            - users.json append (id, registered_at, embedding_index)
            - embeddings.npy에 vstack 후 저장
            - 동명이인은 호출 측 책임
        """
        raise NotImplementedError

    def resolve_unique_name(self, name: str) -> str:
        """동명이인이면 ``name_2`` 식으로 suffix 부여하여 반환. TODO."""
        raise NotImplementedError

    def get_users_and_embeddings(self) -> Tuple[List[str], np.ndarray]:
        """매칭에 쓸 (이름 리스트, 임베딩 행렬) 동시 반환. TODO."""
        raise NotImplementedError

    # ---- 로그 ------------------------------------------------------------
    def append_log(self, user: Optional[str], result: str, reason: str,
                   facenet_score: float, fasnet_score: float) -> None:
        """access_log.csv에 한 줄 append.

        TODO:
            - timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            - csv.writer로 LOG_CSV_HEADER 순서대로 write
        """
        raise NotImplementedError
