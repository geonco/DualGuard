"""신규 사용자 등록 스크립트 (명세서 F1).

카메라로 다양한 각도에서 5~10장을 자동 캡처하여 FaceNet 임베딩의 평균 벡터를
계산하고, users.json 및 embeddings.npy에 저장한다.
"""

from __future__ import annotations


def register_user(name: str) -> None:
    """단일 사용자 등록 처리.

    Args:
        name: 등록할 사용자 이름. 동명이인이면 호출 측에서 ``_2`` 등 suffix 부여.

    TODO:
        - 카메라 오픈
        - REGISTER_NUM_SAMPLES 회 캡처:
            - 얼굴 미검출 시 재시도 안내
            - 얼굴 영역에서 FaceNet 임베딩 추출
        - 임베딩 평균 벡터 계산
        - DataManager로 users.json / embeddings.npy 갱신
    """
    raise NotImplementedError("TODO: 등록 파이프라인 구현")


def main() -> None:
    """CLI 엔트리포인트.

    TODO:
        - argparse 또는 input()으로 사용자 이름 입력
        - 동명이인 검사 → suffix 부여
        - register_user() 호출
        - 완료 메시지 출력
    """
    raise NotImplementedError("TODO: CLI 구현")


if __name__ == "__main__":
    main()
