"""DataManager 단위 테스트.

config의 경로 상수를 tmp_path로 교체해 격리된 환경에서 동작 검증.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

import config
from modules.data_manager import DataManager, EMBEDDING_DIM


@pytest.fixture
def dm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> DataManager:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "USERS_JSON", tmp_path / "users.json")
    monkeypatch.setattr(config, "EMBEDDINGS_NPY", tmp_path / "embeddings.npy")
    monkeypatch.setattr(config, "ACCESS_LOG_CSV", tmp_path / "access_log.csv")
    return DataManager()


def _emb(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal(EMBEDDING_DIM).astype(np.float32)


def test_init_creates_log_with_header(dm: DataManager) -> None:
    assert dm.log_path.exists()
    with open(dm.log_path, encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == config.LOG_CSV_HEADER


def test_load_empty_state(dm: DataManager) -> None:
    assert dm.load_users() == {}
    embs = dm.load_embeddings()
    assert embs.shape == (0, EMBEDDING_DIM)


def test_add_user_persists_both_files(dm: DataManager) -> None:
    idx = dm.add_user("임건우", _emb(0))
    assert idx == 0

    users = dm.load_users()
    assert "임건우" in users
    assert users["임건우"]["id"] == 1
    assert users["임건우"]["embedding_index"] == 0
    assert "registered_at" in users["임건우"]

    embs = dm.load_embeddings()
    assert embs.shape == (1, EMBEDDING_DIM)


def test_add_user_index_increments(dm: DataManager) -> None:
    dm.add_user("a", _emb(1))
    dm.add_user("b", _emb(2))
    idx = dm.add_user("c", _emb(3))
    assert idx == 2
    assert dm.load_embeddings().shape == (3, EMBEDDING_DIM)
    assert dm.load_users()["c"]["id"] == 3


def test_add_user_rejects_wrong_shape(dm: DataManager) -> None:
    with pytest.raises(ValueError):
        dm.add_user("x", np.zeros(256, dtype=np.float32))


def test_add_user_rejects_duplicate_name(dm: DataManager) -> None:
    dm.add_user("임건우", _emb(0))
    with pytest.raises(ValueError):
        dm.add_user("임건우", _emb(1))


def test_resolve_unique_name(dm: DataManager) -> None:
    assert dm.resolve_unique_name("임건우") == "임건우"
    dm.add_user("임건우", _emb(0))
    assert dm.resolve_unique_name("임건우") == "임건우_2"
    dm.add_user("임건우_2", _emb(1))
    assert dm.resolve_unique_name("임건우") == "임건우_3"


def test_get_users_and_embeddings_alignment(dm: DataManager) -> None:
    e0, e1, e2 = _emb(10), _emb(11), _emb(12)
    dm.add_user("a", e0)
    dm.add_user("b", e1)
    dm.add_user("c", e2)

    names, embs = dm.get_users_and_embeddings()
    assert names == ["a", "b", "c"]
    assert embs.shape == (3, EMBEDDING_DIM)
    np.testing.assert_allclose(embs[0], e0)
    np.testing.assert_allclose(embs[1], e1)
    np.testing.assert_allclose(embs[2], e2)


def test_get_users_and_embeddings_empty(dm: DataManager) -> None:
    names, embs = dm.get_users_and_embeddings()
    assert names == []
    assert embs.shape == (0, EMBEDDING_DIM)


def test_append_log_writes_row(dm: DataManager) -> None:
    dm.append_log("임건우", "PASS", "OK", 0.85, 0.92)
    dm.append_log(None, "REJECT", "UnknownUser", 0.42, 0.88)

    with open(dm.log_path, encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert len(rows) == 3
    assert rows[1][1:] == ["임건우", "PASS", "OK", "0.8500", "0.9200"]
    assert rows[2][1] == "Unknown"
    assert rows[2][2:] == ["REJECT", "UnknownUser", "0.4200", "0.8800"]
