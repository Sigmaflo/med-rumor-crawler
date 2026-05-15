# utils/cleaner.py
# 중복 제거, 익명화, 컬럼 통일

import hashlib
import pandas as pd

INPUT_PATH = "data/raw/filtered.csv"
OUTPUT_PATH = "data/processed/result.csv"

COLUMNS = ["platform", "collected_at", "post_date", "url",
           "text", "rumor_type", "keyword_matched", "risk_level"]


def anonymize(text):
    """닉네임·ID를 SHA256 해시로 익명화 (해당 없으면 그대로 반환)"""
    if pd.isna(text):
        return text
    return hashlib.sha256(str(text).encode()).hexdigest()[:10]


def clean_data():
    try:
        df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
        print(f"  {INPUT_PATH} → {len(df)}건 로드")
    except FileNotFoundError:
        print(f"파일 없음: {INPUT_PATH}")
        return

    # URL 기준 중복 제거
    before = len(df)
    df = df.drop_duplicates(subset=["url", "text"])
    print(f"  중복 제거: {before - len(df)}건 제거 → {len(df)}건 남음")

    # 날짜 형식 통일
    df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce").dt.strftime("%Y-%m-%d")

    # 컬럼 정렬
    df = df.reindex(columns=COLUMNS)

    import os
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"전처리 완료: {len(df)}건 → {OUTPUT_PATH}")