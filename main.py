# main.py
# 전체 실행 진입점 — 코드 작성 후 채울 것

from crawlers.youtube import crawl_youtube
from crawlers.dcinside import crawl_dcinside
from utils.filter import filter_rumors
from utils.cleaner import clean_data

def main():
    # 1. 수집
    crawl_youtube()
    crawl_dcinside()

    # 2. 필터링
    filter_rumors()

    # 3. 전처리
    clean_data()

    print("완료: data/processed/result.csv 확인")

if __name__ == "__main__":
    main()
