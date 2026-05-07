"""fusion 단위 테스트 — 명세서 F5 기준."""

from __future__ import annotations

import pytest

from modules.fusion import (
    REASON_OK,
    REASON_SPOOF,
    REASON_UNKNOWN,
    decide_and,
    decide_weighted,
)


# ---- AND --------------------------------------------------------------------


def test_and_pass_when_both_above_threshold() -> None:
    r = decide_and("geonwoo", 0.85, 0.92, 0.7, 0.5)
    assert r.passed
    assert r.reason == REASON_OK
    assert r.user == "geonwoo"


def test_and_reject_unknown_user() -> None:
    r = decide_and(None, 0.42, 0.95, 0.7, 0.5)
    assert not r.passed
    assert r.reason == REASON_UNKNOWN
    assert r.user is None


def test_and_reject_spoof() -> None:
    r = decide_and("geonwoo", 0.85, 0.20, 0.7, 0.5)
    assert not r.passed
    assert r.reason == REASON_SPOOF


def test_and_reject_low_face_even_with_user() -> None:
    # user가 매칭됐지만 점수가 낮은 경계 케이스
    r = decide_and("geonwoo", 0.65, 0.90, 0.7, 0.5)
    assert not r.passed
    assert r.reason == REASON_UNKNOWN


def test_and_threshold_inclusive() -> None:
    r = decide_and("geonwoo", 0.7, 0.5, 0.7, 0.5)
    assert r.passed


# ---- Weighted ---------------------------------------------------------------


def test_weighted_pass_when_combined_above_threshold() -> None:
    # 0.6*0.85 + 0.4*0.90 = 0.87
    r = decide_weighted("geonwoo", 0.85, 0.90, 0.6, 0.4, 0.65)
    assert r.passed
    assert r.reason == REASON_OK


def test_weighted_reject_unknown_user() -> None:
    r = decide_weighted(None, 0.42, 0.95, 0.6, 0.4, 0.65)
    assert not r.passed
    assert r.reason == REASON_UNKNOWN


def test_weighted_reject_low_combined() -> None:
    # 0.6*0.4 + 0.4*0.4 = 0.4 < 0.65
    r = decide_weighted("geonwoo", 0.4, 0.4, 0.6, 0.4, 0.65)
    assert not r.passed
    # 두 점수 동률 → fasnet_score 낮은 쪽이 아니므로 spoof 분기 (>= 비교 시)
    assert r.reason in {REASON_UNKNOWN, REASON_SPOOF}


def test_weighted_attribute_blocker_spoof() -> None:
    # 0.6*0.95 + 0.4*0.10 = 0.61 < 0.65, fasnet 낮음 → SpoofDetected
    r = decide_weighted("geonwoo", 0.95, 0.10, 0.6, 0.4, 0.65)
    assert not r.passed
    assert r.reason == REASON_SPOOF


def test_weighted_attribute_blocker_unknown() -> None:
    # 0.6*0.10 + 0.4*0.95 = 0.44 < 0.65, facenet 낮음 → UnknownUser
    r = decide_weighted("geonwoo", 0.10, 0.95, 0.6, 0.4, 0.65)
    assert not r.passed
    assert r.reason == REASON_UNKNOWN


def test_weighted_threshold_inclusive() -> None:
    # 정확히 임계값 매칭
    r = decide_weighted("geonwoo", 0.65, 0.65, 0.6, 0.4, 0.65)
    assert r.passed
