# utils/filter.py
# 루머 필터링 — 약품명 + 상황 키워드 조합 방식 (루머 1개 = 1줄)

import pandas as pd

RAW_PATHS = ["data/raw/youtube_raw.csv", "data/raw/dcinside_raw.csv"]
OUTPUT_PATH = "data/raw/filtered.csv"

# 유형별 상황 키워드 — 텍스트에 하나라도 포함되면 해당 유형으로 분류
RUMOR_TYPE_KEYWORDS = {
    "1": {  # 병용 위험 무시
        "name": "병용 위험 무시",
        "keywords": ["술", "커피", "에너지음료", "카페인", "음주", "카페", "홍차", "녹차"],
    },
    "2": {  # 과다복용·오용
        "name": "과다복용·오용",
        "keywords": ["많이", "두 배", "두배", "쪼개", "여러 개", "여러개", "한꺼번에", "한번에 많이", "과다"],
    },
    "3": {  # 처방약 공유·유통
        "name": "처방약 공유·유통",
        "keywords": ["나눔", "공유", "빌려", "구함", "구해요", "처방 없이", "처방없이", "무처방"],
    },
    "4": {  # 효능 과장·허위
        "name": "효능 과장·허위",
        "keywords": ["키 크", "집중력", "성적", "머리 좋", "IQ", "공부", "기억력"],
    },
    "5": {  # 단기 감량·근육
        "name": "단기 감량·근육",
        "keywords": ["살 빠", "살빠", "다이어트", "체중", "kg 빠", "체지방", "근육"],
    },
    "6": {  # 해외직구·미인증
        "name": "해외직구·미인증",
        "keywords": ["직구", "해외 구매", "아마존", "iherb", "아이허브", "미인증", "해외직구"],
    },
    "7": {  # 금기 상황 무시
        "name": "금기 상황 무시",
        "keywords": ["빈속", "임신", "수술 전", "수술전", "운전", "음주 후", "공복"],
    },
    "8": {  # 민간요법·대체
        "name": "민간요법·대체",
        "keywords": ["대신", "민간", "자연 치료", "식품으로", "음식으로", "한방", "생강", "마늘"],
    },
}

# 위험도 매핑
RISK_MAP = {
    "1": "높음", "2": "높음", "3": "높음", "7": "높음",
    "4": "중간", "5": "중간", "6": "중간",
    "8": "낮음"
}

# 검색어 → rumor_type 매핑 (키워드 미매칭 시 보완)
KEYWORD_TYPE_MAP = {
    "타이레놀 부작용": "2", "타이레놀 과다복용": "2",
    "감기약 같이 먹어도": "1", "감기약 술": "1",
    "항생제 복용": "2", "항생제 남은 약": "2",
    "수면제 먹어도 돼": "7", "수면제 구하는 법": "3",
    "다이어트약 효과": "5", "다이어트약 직구": "6",
    "ADHD약 공유": "3", "진통제 과다복용": "2",
    "영양제 효과 있다": "4", "보충제 부작용": "6",
    "타이레놀": "2", "감기약": "1", "항생제": "2",
    "수면제": "3", "진통제": "2", "다이어트약": "5",
    "ADHD약": "3", "영양제": "4", "보충제": "6",
}


def classify_rumor_type(text):
    """텍스트에서 매칭되는 루머 유형 목록 반환 (유형별 키워드 조합)"""
    matched = []
    for rumor_type, info in RUMOR_TYPE_KEYWORDS.items():
        for kw in info["keywords"]:
            if kw in text:
                matched.append((rumor_type, kw))
                break  # 유형당 1개만
    return matched


def extract_rumor_rows(row):
    """게시글에서 유형별로 행 분리 (루머 1개 = 1줄)"""
    text = str(row["text"])
    matched_types = classify_rumor_type(text)
    if not matched_types:
        return []

    rows = []
    for rumor_type, matched_kw in matched_types:
        new_row = row.to_dict()
        new_row["rumor_type"] = rumor_type
        new_row["rumor_pattern"] = matched_kw
        rows.append(new_row)
    return rows


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

    # 유형별 키워드 조합으로 루머 분류 및 행 분리
    expanded = []
    for _, row in df.iterrows():
        expanded.extend(extract_rumor_rows(row))

    if not expanded:
        print("루머 패턴 매칭 결과 없음")
        return

    df = pd.DataFrame(expanded)
    print(f"루머 분류: {len(df)}줄 생성")

    # 위험도 태깅
    df["risk_level"] = df["rumor_type"].map(RISK_MAP).fillna("미분류")

    # 컬럼 순서 정렬
    columns = ["platform", "collected_at", "post_date", "url", "text",
               "rumor_type", "keyword_matched", "rumor_pattern", "risk_level"]
    df = df.reindex(columns=columns)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"필터링 완료: {len(df)}줄 → {OUTPUT_PATH}")