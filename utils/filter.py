# utils/filter.py
# 루머 키워드 필터링 및 위험도 태깅 (루머 1개 = 1줄)

import pandas as pd

RAW_PATHS = ["data/raw/youtube_raw.csv", "data/raw/dcinside_raw.csv"]
OUTPUT_PATH = "data/raw/filtered.csv"

# 복약 맥락 필터 — 이 중 하나라도 없으면 제외
MEDICAL_CONTEXT = [
    "약", "복용", "먹다", "먹어", "복약",
    "성분", "용량", "처방", "약물", "약품",
    "진통제", "항생제", "수면제", "영양제", "보충제"
]

# 단정 표현 패턴 — 루머 유형 8개에 1:1 매핑
RUMOR_PATTERNS = {
    "같이 먹어도":   "1",  # 병용 위험 무시
    "더 먹어도 돼":  "2",  # 과다복용·오용
    "약 줘도 돼":    "3",  # 처방약 공유·유통
    "먹으면 효과":   "4",  # 효능 과장·허위
    "먹으면 살":     "5",  # 단기 감량·근육
    "직구 약 좋다":  "6",  # 해외직구·미인증
    "먹어도 괜찮아": "7",  # 금기 상황 무시
    "약 대신 먹어":  "8",  # 민간요법·대체
}

# 단순 질문 패턴 (제외)
QUESTION_PATTERNS = [
    "되나요", "괜찮을까요", "추천해주세요", "어떻게 생각",
    "해도 될까요", "먹어도 될까", "괜찮나요", "어떤가요"
]

# 검색어 → rumor_type 매핑
KEYWORD_TYPE_MAP = {
    # 유튜브 검색어
    "타이레놀 부작용": "2",
    "타이레놀 과다복용": "2",
    "감기약 같이 먹어도": "1",
    "감기약 술": "1",
    "항생제 복용": "2",
    "항생제 남은 약": "2",
    "수면제 먹어도 돼": "7",
    "수면제 구하는 법": "3",
    "다이어트약 효과": "5",
    "다이어트약 직구": "6",
    "ADHD약 공유": "3",
    "진통제 과다복용": "2",
    "영양제 효과 있다": "4",
    "보충제 부작용": "6",
    # 디시인사이드 검색어
    "타이레놀": "2",
    "감기약": "1",
    "항생제": "2",
    "수면제": "3",
    "진통제": "2",
    "다이어트약": "5",
    "ADHD약": "3",
    "영양제": "4",
    "보충제": "6",
}

# 위험도 매핑
RISK_MAP = {
    "1": "높음", "2": "높음", "3": "높음", "7": "높음",
    "4": "중간", "5": "중간", "6": "중간",
    "8": "낮음"
}


def has_medical_context(text):
    """복약 관련 단어가 하나라도 있는지 확인"""
    return any(word in text for word in MEDICAL_CONTEXT)


def is_question(text):
    """단순 질문 여부 확인"""
    return any(p in text for p in QUESTION_PATTERNS)


def extract_rumor_rows(row):
    """게시글에서 감지된 루머 패턴별로 행 분리 (루머 1개 = 1줄)"""
    text = str(row["text"])
    if is_question(text):
        return []

    rows = []
    for pattern, pattern_type in RUMOR_PATTERNS.items():
        if pattern in text:
            new_row = row.to_dict()
            new_row["rumor_pattern"] = pattern
            # 패턴에서 rumor_type 직접 결정
            new_row["rumor_type"] = pattern_type
            rows.append(new_row)
    return rows


def normalize_rumor_type(val, keyword):
    """rumor_type 보완 — 패턴 미매칭 시 검색어로 추론"""
    if pd.notna(val) and str(val).strip() not in ("", "nan"):
        try:
            return str(int(float(val)))
        except ValueError:
            pass
    return KEYWORD_TYPE_MAP.get(str(keyword).strip(), "")


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

    # 2차: 루머 패턴별 행 분리 (루머 1개 = 1줄)
    expanded = []
    for _, row in df.iterrows():
        expanded.extend(extract_rumor_rows(row))

    if not expanded:
        print("루머 패턴 매칭 결과 없음")
        return

    df = pd.DataFrame(expanded)
    print(f"루머 패턴 분리: {len(df)}줄 생성")

    # rumor_type 정규화
    df["rumor_type"] = df.apply(
        lambda row: normalize_rumor_type(row["rumor_type"], row["keyword_matched"]), axis=1
    )

    # 위험도 태깅
    df["risk_level"] = df["rumor_type"].map(RISK_MAP).fillna("미분류")

    # 컬럼 순서 정렬
    columns = ["platform", "collected_at", "post_date", "url", "text",
               "rumor_type", "keyword_matched", "rumor_pattern", "risk_level"]
    df = df.reindex(columns=columns)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"필터링 완료: {len(df)}줄 → {OUTPUT_PATH}")