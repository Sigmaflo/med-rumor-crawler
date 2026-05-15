# utils/filter.py
# 루머 키워드 필터링 및 위험도 태깅

import pandas as pd

RAW_PATHS = ["data/raw/youtube_raw.csv", "data/raw/dcinside_raw.csv"]
OUTPUT_PATH = "data/raw/filtered.csv"

# 복약 맥락 필터 — 이 중 하나라도 없으면 제외
MEDICAL_CONTEXT = [
    "약", "복용", "먹다", "먹어", "복약",
    "성분", "용량", "처방", "약물", "약품",
    "진통제", "항생제", "수면제", "영양제", "보충제"
]

# 단정 표현 패턴 (루머 포함)
RUMOR_PATTERNS = [
    "해도 돼", "괜찮아", "된다더라", "보장된다", "무조건",
    "효과 있다", "먹어봤는데", "친구가 그러는데", "확실히",
    "무조건 돼", "걱정 마", "문제없어"
]

# 단순 질문 패턴 (제외)
QUESTION_PATTERNS = [
    "되나요", "괜찮을까요", "추천해주세요", "어떻게 생각",
    "해도 될까요", "먹어도 될까", "괜찮나요", "어떤가요"
]

# 위험도 매핑
RISK_MAP = {
    "1": "높음", "2": "높음", "3": "높음", "7": "높음",
    "4": "중간", "5": "중간", "6": "중간",
    "8": "낮음"
}


def has_medical_context(text):
    """복약 관련 단어가 하나라도 있는지 확인"""
    return any(word in text for word in MEDICAL_CONTEXT)


def is_rumor(text):
    """단정 표현 포함 AND 단순 질문 아닌 경우 → 루머"""
    has_rumor = any(p in text for p in RUMOR_PATTERNS)
    is_question = any(p in text for p in QUESTION_PATTERNS)
    return has_rumor and not is_question


def filter_rumors():
    dfs = []
    for path in RAW_PATHS:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
            dfs.append(df)
            print(f"  {path} → {len(df)}건 로드")
        except FileNotFoundError:
            print(f"  파일 없음 (건너뜀): {path}")

    if not dfs:
        print("수집된 데이터가 없습니다.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"\n전체 {len(df)}건 로드 완료")

    # 1차: 복약 맥락 필터
    before = len(df)
    df = df[df["text"].apply(lambda x: has_medical_context(str(x)))]
    print(f"복약 맥락 필터: {before - len(df)}건 제외 → {len(df)}건 남음")

    # 2차: 루머 필터링
    df["is_rumor"] = df["text"].apply(lambda x: is_rumor(str(x)))
    before = len(df)
    df = df[df["is_rumor"]].drop(columns=["is_rumor"])
    print(f"루머 필터: {before - len(df)}건 제외 → {len(df)}건 남음")

    # 위험도 태깅 (float → int → str 변환으로 버그 수정)
    df["risk_level"] = (
        df["rumor_type"]
        .apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).strip() != "" else "")
        .map(RISK_MAP)
        .fillna("미분류")
    )

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"필터링 완료: {len(df)}건 → {OUTPUT_PATH}")