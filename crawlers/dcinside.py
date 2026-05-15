# crawlers/dcinside.py
# requests + BeautifulSoup4 기반 디시인사이드 검색 수집 (테스트용)

import os
import csv
import json
import time
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 테스트 설정
# SEARCH_KEYWORDS = [
#     "타이레놀", "감기약", "항생제",
#     "수면제", "진통제", "다이어트약",
#     "ADHD약", "영양제", "보충제"
# ]
SEARCH_KEYWORDS = [
    "타이레놀",
    "감기약",
]
TEST_PAGES = 1  # 검색어당 페이지 수

OUTPUT_PATH = "data/raw/dcinside_raw.csv"
KEYWORDS_PATH = "keywords.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def load_keywords():
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_posts(search_keyword, page=1):
    """검색어로 디시인사이드 게시글 URL 추출"""
    url = f"https://search.dcinside.com/post/p/{page}/q/{search_keyword}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        posts = []
        for a in soup.select("ul.sch_result_list li a"):
            href = a.get("href", "")
            if href and "gall.dcinside.com" in href:
                posts.append(href)

        print(f"  [{search_keyword} / p{page}] 게시글 {len(posts)}개 발견")
        return posts
    except Exception as e:
        print(f"  검색 실패 ({search_keyword}): {e}")
        return []


def get_post_content(url, keywords_flat, search_keyword):
    """게시글 본문 수집 + 루머 키워드 매칭"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 본문
        body = soup.select_one("div.write_div")
        text = body.get_text(strip=True) if body else ""

        # 작성일
        date_tag = soup.select_one("span.gall_date")
        post_date = date_tag["title"][:10] if date_tag and date_tag.get("title") else ""

        # 루머 키워드 매칭
        matched_type = ""
        matched_keyword = ""
        for rumor_type, kw_list in keywords_flat.items():
            for kw in kw_list:
                if kw in text:
                    matched_type = rumor_type
                    matched_keyword = kw
                    break
            if matched_type:
                break

        # 루머 키워드 미매칭이면 검색어 자체를 keyword_matched로 저장
        if not matched_keyword:
            matched_keyword = search_keyword

        if not text:
            return None

        return {
            "platform": "dcinside",
            "collected_at": datetime.today().strftime("%Y-%m-%d"),
            "post_date": post_date,
            "url": url,
            "text": text[:500],
            "rumor_type": matched_type,
            "keyword_matched": matched_keyword,
            "risk_level": "",
        }
    except Exception as e:
        print(f"  수집 실패: {url} → {e}")
        return None


def crawl_dcinside():
    keywords = load_keywords()
    all_rows = []

    for search_keyword in SEARCH_KEYWORDS:
        print(f"\n[검색어: {search_keyword}]")
        for page in range(1, TEST_PAGES + 1):
            urls = search_posts(search_keyword, page)

            for url in urls:
                row = get_post_content(url, keywords, search_keyword)
                if row:
                    all_rows.append(row)
                    print(f"  수집: {row['keyword_matched']} | {row['text'][:30]}...")
                time.sleep(random.uniform(1, 2))

    # CSV 저장
    os.makedirs("data/raw", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["platform", "collected_at", "post_date", "url", "text",
                      "rumor_type", "keyword_matched", "risk_level"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n디시인사이드 수집 완료: 총 {len(all_rows)}건 → {OUTPUT_PATH}")