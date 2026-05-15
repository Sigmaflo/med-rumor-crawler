# 청소년 온라인 복약 루머 위험도 분석 — 2번 크롤러

유튜브 댓글 및 디시인사이드 게시글을 수집하여 복약 관련 루머를 탐지·분류하는 크롤러입니다.

---

## 담당 플랫폼

| 플랫폼 | 수집 방식 | 비용 | 상태 |
|--------|-----------|------|------|
| YouTube 댓글 | YouTube Data API v3 | 무료 (10,000유닛/일) | 구현 완료 |
| 디시인사이드 | requests + BeautifulSoup4 | 무료 | 구현 완료 |
| 트위터/X | Twitter API v2 | 유료 (Basic $100/월~) | ⏸ 추후 구현 (비용 문제로 보류) |

---

## 프로젝트 구조

```
med-rumor-crawler/
├── .env                  # API 키 (절대 깃에 올리지 말 것)
├── .env.example          # API 키 양식
├── .gitignore
├── requirements.txt
├── keywords.json         # 루머 유형별 키워드 목록
├── crawlers/
│   ├── youtube.py        # 유튜브 댓글 수집
│   └── dcinside.py       # 디시인사이드 검색 수집
├── utils/
│   ├── filter.py         # 루머 필터링 및 유형 태깅
│   └── cleaner.py        # 전처리 (중복 제거, 플랫폼별 저장)
├── data/
│   ├── raw/              # 수집 원본 CSV (깃 제외)
│   └── processed/        # 전처리 완료 CSV (깃 제외)
└── main.py               # 전체 실행 진입점
```

---

## 전처리 파이프라인

```
수집
  youtube.py  →  data/raw/youtube_raw.csv
  dcinside.py →  data/raw/dcinside_raw.csv
       ↓
filter.py
  1단계: 유형별 상황 키워드 조합으로 루머 분류
         유형 1 병용 위험  → 술, 커피, 에너지음료, 카페인 ...
         유형 2 과다복용   → 많이, 두배, 쪼개, 과다 ...
         유형 3 처방약공유 → 나눔, 공유, 빌려, 처방없이 ...
         유형 4 효능과장   → 키 크, 집중력, 성적, 기억력 ...
         유형 5 단기감량   → 살빠, 다이어트, 체중, 체지방 ...
         유형 6 해외직구   → 직구, 아마존, 아이허브 ...
         유형 7 금기무시   → 빈속, 임신, 수술전, 공복 ...
         유형 8 민간요법   → 대신, 민간, 한방, 생강 ...
  2단계: 루머 1개 = 1줄로 행 분리
  3단계: rumor_type · risk_level 태깅
       ↓
cleaner.py
  - URL + rumor_pattern 기준 중복 제거
  - 날짜 형식 통일 (YYYY-MM-DD)
  - 플랫폼별 분리 저장
       ↓
결과
  data/processed/youtube_result.csv
  data/processed/dcinside_result.csv
```

---

## 루머 분류 기준 (유형별 키워드 조합)

텍스트에 아래 키워드 중 하나라도 포함되면 해당 유형으로 분류됩니다.

| 유형 | 유형명 | 분류 키워드 | 위험도 |
|------|--------|-------------|--------|
| 1 | 병용 위험 무시 | 술, 커피, 에너지음료, 카페인, 음주 | 높음 |
| 2 | 과다복용·오용 | 많이, 두배, 쪼개, 여러개, 과다 | 높음 |
| 3 | 처방약 공유·유통 | 나눔, 공유, 빌려, 처방없이, 구함 | 높음 |
| 4 | 효능 과장·허위 | 키 크, 집중력, 성적, 기억력, IQ | 중간 |
| 5 | 단기 감량·근육 | 살빠, 다이어트, 체중, 체지방, 근육 | 중간 |
| 6 | 해외직구·미인증 | 직구, 아마존, 아이허브, 미인증 | 중간 |
| 7 | 금기 상황 무시 | 빈속, 임신, 수술전, 공복, 운전 | 높음 |
| 8 | 민간요법·대체 | 대신, 민간, 한방, 생강, 마늘 | 낮음 |

---

## 수집 데이터 구조 (CSV 컬럼)

팀 전체 공통 포맷입니다. 병합 시 컬럼명을 반드시 통일하세요.

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `platform` | 수집 플랫폼 | `youtube` / `dcinside` |
| `collected_at` | 수집 날짜 | `2026-05-15` |
| `post_date` | 원글 작성일 | `2026-03-01` |
| `url` | 원문 링크 | `https://...` |
| `text` | 본문 또는 댓글 내용 | `타이레놀 두 개 먹어도 돼` |
| `rumor_type` | 루머 유형 번호 | `2` |
| `keyword_matched` | 매칭된 검색어 | `타이레놀` |
| `rumor_pattern` | 감지된 루머 패턴 | `더 먹어도 돼` |
| `risk_level` | 위험도 | `높음` / `중간` / `낮음` |

---

## 설치 및 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 2. 의존성 설치
pip install -r requirements.txt

# 3. API 키 설정
cp .env.example .env
# .env 파일 열어서 YOUTUBE_API_KEY 입력

# 4. 실행
python main.py
```

> YouTube Data API v3 키 발급:
> Google Cloud Console → 프로젝트 생성 → API 활성화 → 사용자 인증 정보 → API 키 생성

---

## 크롤링 주의사항

- 요청 간 **1~2.5초 랜덤 딜레이** 필수 (IP 차단 방지)
- User-Agent 헤더 반드시 설정
- YouTube API 유닛 소모 주의: `search.list` 1회 = 100유닛 (하루 10,000유닛 한도)
- `.env` 파일을 `.gitignore`에 반드시 추가
- `data/` 폴더는 `.gitignore`로 깃 제외 — 결과 파일은 구글 드라이브로 공유

---

## 팀 협의 사항

- [ ] CSV 컬럼 구조 최종 확정 (1번·3번 담당자와 통일)
- [ ] `rumor_type` 태깅 기준 문서화
- [ ] 수집 기간 범위 합의 (예: 최근 1년)
- [ ] 결과 파일 공유 방식 결정 (구글 드라이브 권장)

---

## 담당자

- 2번 역할: 유튜브 댓글 + 디시인사이드
- 문의: 팀 채널로 연락