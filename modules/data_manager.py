"""데이터 영속성 관리 (명세서 4.3, F6).

users.json, embeddings.npy, access_log.csv의 입출력을 캡슐화한다.
직접 np.load / json.load 하지 말고 이 클래스만 거쳐서 사용한다 — users.json의
embedding_index와 embeddings.npy의 행 번호가 1:1로 매핑되어야 하므로 한쪽만
갱신하면 인덱스가 어긋난다.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

import config

EMBEDDING_DIM = 512


class DataManager:
    """JSON / numpy / CSV 통합 데이터 레이어."""

    def __init__(self) -> None:
        self.users_path = config.USERS_JSON
        self.embeddings_path = config.EMBEDDINGS_NPY
        self.log_path = config.ACCESS_LOG_CSV

        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(config.LOG_CSV_HEADER)

    # ---- 사용자 ----------------------------------------------------------
    def load_users(self) -> Dict[str, dict]:
        if not self.users_path.exists():
            return {}
        with open(self.users_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_embeddings(self) -> np.ndarray:
        if not self.embeddings_path.exists():
            return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
        return np.load(self.embeddings_path)

    def _save_users(self, users: Dict[str, dict]) -> None:
        with open(self.users_path, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    def _save_embeddings(self, embeddings: np.ndarray) -> None:
        np.save(self.embeddings_path, embeddings.astype(np.float32))

    def add_user(self, name: str, mean_embedding: np.ndarray) -> int:
        """신규 사용자 추가. embedding_index 반환.

        users.json과 embeddings.npy를 한 트랜잭션처럼 같이 갱신한다.
        동명이인 검사는 호출 측에서 resolve_unique_name으로 미리 처리.
        """
        if mean_embedding.shape != (EMBEDDING_DIM,):
            raise ValueError(
                f"embedding shape must be ({EMBEDDING_DIM},), got {mean_embedding.shape}"
            )

        users = self.load_users()
        if name in users:
            raise ValueError(f"user already exists: {name} (use resolve_unique_name first)")

        embeddings = self.load_embeddings()
        new_index = embeddings.shape[0]
        embeddings = np.vstack([embeddings, mean_embedding[None, :].astype(np.float32)])

        next_id = max((u["id"] for u in users.values()), default=0) + 1
        users[name] = {
            "id": next_id,
            "registered_at": datetime.now().strftime("%Y-%m-%d"),
            "embedding_index": new_index,
        }

        self._save_embeddings(embeddings)
        self._save_users(users)
        return new_index

    def resolve_unique_name(self, name: str) -> str:
        """동명이인이면 ``name_2``, ``name_3`` ... 식으로 suffix 부여."""
        users = self.load_users()
        if name not in users:
            return name
        i = 2
        while f"{name}_{i}" in users:
            i += 1
        return f"{name}_{i}"

    def get_users_and_embeddings(self) -> Tuple[List[str], np.ndarray]:
        """매칭용 (이름 리스트, 임베딩 행렬) 반환.

        리스트 인덱스 = 임베딩 행 인덱스. embedding_index 기준으로 정렬한다.
        """
        users = self.load_users()
        embeddings = self.load_embeddings()
        if not users:
            return [], embeddings

        ordered = sorted(users.items(), key=lambda kv: kv[1]["embedding_index"])
        names = [name for name, _ in ordered]
        return names, embeddings

    # ---- 로그 ------------------------------------------------------------
    def append_log(
        self,
        user: Optional[str],
        result: str,
        reason: str,
        facenet_score: float,
        fasnet_score: float,
    ) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            user if user else "Unknown",
            result,
            reason,
            f"{facenet_score:.4f}",
            f"{fasnet_score:.4f}",
        ]
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
