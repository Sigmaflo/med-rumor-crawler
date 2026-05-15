# crawlers/youtube.py
# YouTube Data API v3 기반 댓글 수집 (테스트용)

import os
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

# 테스트 설정
MAX_VIDEOS_PER_KEYWORD = 3   # 키워드당 영상 수
MAX_COMMENTS_PER_VIDEO = 10  # 영상당 댓글 수
TEST_KEYWORD_INDEX = 0       # 유형별 첫 번째 키워드만 사용

OUTPUT_PATH = "data/raw/youtube_raw.csv"
KEYWORDS_PATH = "keywords.json"


def load_keywords():
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_videos(youtube, keyword):
    """키워드로 영상 검색 → video_id 목록 반환"""
    response = youtube.search().list(
        q=keyword,
        part="id",
        type="video",
        maxResults=MAX_VIDEOS_PER_KEYWORD,
        relevanceLanguage="ko",
    ).execute()

    video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
    print(f"  [{keyword}] 영상 {len(video_ids)}개 검색됨")
    return video_ids


def fetch_comments(youtube, video_id, keyword, rumor_type):
    """video_id별 댓글 수집 → 딕셔너리 리스트 반환"""
    results = []
    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=MAX_COMMENTS_PER_VIDEO,
            textFormat="plainText",
        ).execute()

        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            results.append({
                "platform": "youtube",
                "collected_at": datetime.today().strftime("%Y-%m-%d"),
                "post_date": snippet["publishedAt"][:10],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "text": snippet["textDisplay"],
                "rumor_type": rumor_type,
                "keyword_matched": keyword,
                "risk_level": "",  # filter.py에서 채움
            })
    except Exception as e:
        print(f"  댓글 수집 실패 (video_id={video_id}): {e}")

    return results


def crawl_youtube():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("오류: .env에 YOUTUBE_API_KEY가 없습니다.")
        return

    youtube = build("youtube", "v3", developerKey=api_key)
    keywords = load_keywords()

    all_rows = []

    for rumor_type, keyword_list in keywords.items():
        keyword = keyword_list[TEST_KEYWORD_INDEX]  # 유형별 첫 번째 키워드만
        print(f"\n[유형 {rumor_type}] 키워드: {keyword}")

        video_ids = search_videos(youtube, keyword)

        for video_id in video_ids:
            comments = fetch_comments(youtube, video_id, keyword, rumor_type)
            all_rows.extend(comments)
            print(f"  video_id={video_id} → 댓글 {len(comments)}개 수집")
            time.sleep(1)  # API 요청 간 딜레이

    # CSV 저장
    os.makedirs("data/raw", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["platform", "collected_at", "post_date", "url", "text",
                      "rumor_type", "keyword_matched", "risk_level"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n유튜브 수집 완료: 총 {len(all_rows)}건 → {OUTPUT_PATH}")