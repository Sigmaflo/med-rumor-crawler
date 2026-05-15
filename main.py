# main.py
# 전체 실행 진입점

import os
import pandas as pd
from crawlers.youtube import crawl_youtube
from crawlers.dcinside import crawl_dcinside
from utils.filter import filter_rumors
from utils.cleaner import clean_data

def main():
    print("=" * 40)
    print("1단계: 데이터 수집")
    print("=" * 40)
    crawl_youtube()
    crawl_dcinside()

    print("\n" + "=" * 40)
    print("2단계: 루머 필터링")
    print("=" * 40)
    filter_rumors()

    print("\n" + "=" * 40)
    print("3단계: 전처리")
    print("=" * 40)
    clean_data()

    print("\n" + "=" * 40)
    print("완료 요약")
    print("=" * 40)
    for platform in ["youtube", "dcinside"]:
        result_path = f"data/processed/{platform}_result.csv"
        if os.path.exists(result_path):
            df = pd.read_csv(result_path, encoding="utf-8-sig")
            print(f"\n[{platform}] 총 {len(df)}건")
            print(f"유형별:\n{df['rumor_type'].value_counts().sort_index().to_string()}")
            print(f"위험도별:\n{df['risk_level'].value_counts().to_string()}")
            print(f"결과 파일: {result_path}")
        else:
            print(f"[{platform}] 결과 파일 없음")

if __name__ == "__main__":
    main()