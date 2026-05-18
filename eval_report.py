"""Aggregate eval_log.csv into report tables (spec 9.3).

Outputs two markdown tables ready to paste into the final report:
  1) Pass rate per scenario for FaceNet-only / MiniFASNet-only / Dual (AND, Weighted)
  2) Mean facenet_score and fasnet_score per scenario

Each row in eval_log.csv represents one capture attempt with raw scores +
single/dual pass flags, so both tables fall out of the same data.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from statistics import mean

import config

LABELS = ("real_self", "phone_self", "phone_other")
LABEL_PRETTY = {
    "real_self": "Real face (self)",
    "phone_self": "Phone photo (self)",
    "phone_other": "Phone photo (other)",
}
EXPECTED = {
    "real_self": "PASS",
    "phone_self": "BLOCK",
    "phone_other": "BLOCK",
}


def _pct(num: int, denom: int) -> str:
    if denom == 0:
        return "n/a"
    return f"{100.0 * num / denom:.0f}%"


def _success_rate(label: str, flag: int, rows: list[dict]) -> str:
    """Return % of trials where the system did the *correct* thing.

    For real_self the correct outcome is pass=1; for phone_* it's pass=0.
    """
    sub = [r for r in rows if r["label"] == label]
    if not sub:
        return "n/a"
    want_pass = (EXPECTED[label] == "PASS")
    hits = sum(1 for r in sub if bool(int(r[flag])) == want_pass)
    return _pct(hits, len(sub))


def main() -> None:
    path = config.DATA_DIR / "eval_log.csv"
    if not path.exists():
        raise SystemExit(f"no eval log: {path}")

    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit("eval_log.csv is empty")

    counts = defaultdict(int)
    for r in rows:
        counts[r["label"]] += 1

    print("# DualGuard Evaluation Report")
    print()
    print(f"Total samples: {len(rows)}  " + ", ".join(
        f"{LABEL_PRETTY.get(k, k)}={v}" for k, v in counts.items()
    ))
    print()

    # Table 1 - correctness rate per scenario (spec 9.3 Table 1 shape)
    print("## Table 1. Correct-decision rate by scenario")
    print()
    print("| Scenario | Expected | FaceNet only | MiniFASNet only | Dual (AND) | Dual (Weighted) |")
    print("|---|---|---|---|---|---|")
    for lbl in LABELS:
        if counts[lbl] == 0:
            continue
        print(
            f"| {LABEL_PRETTY[lbl]} | {EXPECTED[lbl]} "
            f"| {_success_rate(lbl, 'face_pass', rows)} "
            f"| {_success_rate(lbl, 'fas_pass', rows)} "
            f"| {_success_rate(lbl, 'dual_and_pass', rows)} "
            f"| {_success_rate(lbl, 'dual_weighted_pass', rows)} |"
        )
    print()
    print(
        f"Thresholds: FaceNet >= {config.FACENET_SIM_THRESHOLD}, "
        f"MiniFASNet >= {config.FASNET_REAL_THRESHOLD}, "
        f"Weighted alpha={config.FUSION_ALPHA} beta={config.FUSION_BETA} "
        f"tau={config.FUSION_COMBINED_THRESHOLD}."
    )
    print()

    # Table 2 - mean raw scores per scenario
    print("## Table 2. Mean raw scores")
    print()
    print("| Scenario | n | mean facenet_score | mean fasnet_score |")
    print("|---|---|---|---|")
    for lbl in LABELS:
        sub = [r for r in rows if r["label"] == lbl]
        if not sub:
            continue
        mf = mean(float(r["facenet_score"]) for r in sub)
        ms = mean(float(r["fasnet_score"]) for r in sub)
        print(f"| {LABEL_PRETTY[lbl]} | {len(sub)} | {mf:.3f} | {ms:.3f} |")
    print()


if __name__ == "__main__":
    main()
