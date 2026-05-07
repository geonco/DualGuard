"""FaceRecognizer 단위 테스트.

실제 FaceNet 모델은 로딩이 무거우므로 매칭/정규화 로직은 모델 mocking으로 검증.
임베딩 추출(embed)은 통합테스트(Pi에서 실제 카메라)로 확인.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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


@pytest.fixture
def recognizer(dm: DataManager):
    """InceptionResnetV1 로딩을 우회 — 매칭 로직만 검증."""
    with patch("modules.face_recognizer.InceptionResnetV1") as mock_model_cls:
        mock_model_cls.return_value.eval.return_value.to.return_value = None
        from modules.face_recognizer import FaceRecognizer

        rec = FaceRecognizer(threshold=0.7, data_manager=dm)
        return rec


def _unit_vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
    return v / np.linalg.norm(v)


def test_l2_normalize() -> None:
    from modules.face_recognizer import FaceRecognizer

    x = np.array([[3.0, 4.0], [1.0, 0.0]], dtype=np.float32)
    n = FaceRecognizer._l2_normalize(x)
    np.testing.assert_allclose(np.linalg.norm(n, axis=1), [1.0, 1.0], atol=1e-5)


def test_match_empty_db_returns_none(recognizer) -> None:
    name, score = recognizer.match(_unit_vec(0))
    assert name is None
    assert score == 0.0


def test_match_returns_self_above_threshold(recognizer, dm: DataManager) -> None:
    target = _unit_vec(42)
    dm.add_user("임건우", target)
    recognizer.reload_database()

    name, score = recognizer.match(target)
    assert name == "임건우"
    assert score == pytest.approx(1.0, abs=1e-5)


def test_match_returns_none_below_threshold(recognizer, dm: DataManager) -> None:
    dm.add_user("임건우", _unit_vec(1))
    recognizer.reload_database()

    # 완전히 다른 방향의 벡터
    name, score = recognizer.match(_unit_vec(999))
    assert name is None
    assert score < 0.7


def test_match_picks_argmax_among_multiple(recognizer, dm: DataManager) -> None:
    a, b, c = _unit_vec(1), _unit_vec(2), _unit_vec(3)
    dm.add_user("a", a)
    dm.add_user("b", b)
    dm.add_user("c", c)
    recognizer.reload_database()

    name, score = recognizer.match(b)
    assert name == "b"
    assert score == pytest.approx(1.0, abs=1e-5)


def test_reload_database_picks_up_new_user(recognizer, dm: DataManager) -> None:
    target = _unit_vec(7)
    # 등록 전에는 빈 DB
    name, _ = recognizer.match(target)
    assert name is None

    dm.add_user("new", target)
    recognizer.reload_database()
    name, _ = recognizer.match(target)
    assert name == "new"


def test_threshold_override(dm: DataManager) -> None:
    """엄격한 임계값(0.99)에서는 살짝 다른 벡터도 거절돼야 함."""
    with patch("modules.face_recognizer.InceptionResnetV1") as mock_model_cls:
        mock_model_cls.return_value.eval.return_value.to.return_value = None
        from modules.face_recognizer import FaceRecognizer

        rec = FaceRecognizer(threshold=0.99, data_manager=dm)

        target = _unit_vec(0)
        dm.add_user("u", target)
        rec.reload_database()

        # 동일 벡터는 통과
        name, _ = rec.match(target)
        assert name == "u"

        # 살짝 노이즈 추가하면 0.99 미만 → 거절
        noisy = target + 0.3 * _unit_vec(1)
        noisy = noisy / np.linalg.norm(noisy)
        name, score = rec.match(noisy)
        assert name is None
        assert score < 0.99
