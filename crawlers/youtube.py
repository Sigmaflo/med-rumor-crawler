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
SEARCH_KEYWORDS = [
    "타이레놀 부작용",
    "감기약 같이 먹어도",
    "항생제 복용",
    "수면제 먹어도 돼",
    "다이어트약 효과",
    "ADHD약 공유",
    "진통제 과다복용",
    # 추가 7개
    "타이레놀 과다복용",
    "감기약 술",
    "항생제 남은 약",
    "수면제 구하는 법",
    "다이어트약 직구",
    "영양제 효과 있다",
    "보충제 부작용",
]
MAX_VIDEOS_PER_KEYWORD = 6   # 키워드당 영상 수
MAX_COMMENTS_PER_VIDEO = 50  # 영상당 댓글 수

OUTPUT_PATH = "data/raw/youtube_raw.csv"


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


def fetch_comments(youtube, video_id, keyword):
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
                "rumor_type": "",        # filter.py에서 채움
                "keyword_matched": keyword,
                "risk_level": "",        # filter.py에서 채움
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
    all_rows = []

    for keyword in SEARCH_KEYWORDS:
        print(f"\n[검색어: {keyword}]")
        video_ids = search_videos(youtube, keyword)

        for video_id in video_ids:
            comments = fetch_comments(youtube, video_id, keyword)
            all_rows.extend(comments)
            print(f"  video_id={video_id} → 댓글 {len(comments)}개 수집")
            time.sleep(1)

    # CSV 저장
    os.makedirs("data/raw", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["platform", "collected_at", "post_date", "url", "text",
                      "rumor_type", "keyword_matched", "risk_level"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n유튜브 수집 완료: 총 {len(all_rows)}건 → {OUTPUT_PATH}")