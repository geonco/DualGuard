# DualGuard Evaluation Report

Total samples: 30  Real face (self)=10, Phone photo (self)=10, Phone photo (other)=10

## Table 1. Correct-decision rate by scenario

| Scenario | Expected | FaceNet only | MiniFASNet only | Dual (AND) | Dual (Weighted) |
|---|---|---|---|---|---|
| Real face (self) | PASS | 100% | 100% | 100% | 100% |
| Phone photo (self) | BLOCK | 0% | 100% | 100% | 100% |
| Phone photo (other) | BLOCK | 100% | 100% | 100% | 100% |

Thresholds: FaceNet >= 0.7, MiniFASNet >= 0.5, Weighted alpha=0.6 beta=0.4 tau=0.65.

## Table 2. Mean raw scores

| Scenario | n | mean facenet_score | mean fasnet_score |
|---|---|---|---|
| Real face (self) | 10 | 0.925 | 1.000 |
| Phone photo (self) | 10 | 0.876 | 0.038 |
| Phone photo (other) | 10 | 0.614 | 0.000 |

