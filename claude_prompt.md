# 한국 인기 영화 섹션 — 백엔드 랜덤 추출 방식으로 변경

## 문제
한국 인기 영화만 popularity DESC 고정 정렬이라 새로고침해도 항상 동일한 영화 동일한 순서.
인기 영화/높은 평점 섹션은 이미 Top 100 → random.sample(50) + shuffle 방식으로 구현되어 있음.
한국 인기 영화도 동일한 방식으로 통일.

## 수정

### 1. 백엔드: 한국 인기 영화를 recommendations.py에서 처리

현재 한국 인기 영화는 프론트에서 `getMovies({ country: "대한민국", sort_by: "popularity" })`로
movies.py의 범용 검색 엔드포인트를 직접 호출하고 있음.

이것을 인기/높은평점과 동일하게 recommendations.py에서 전용 로직으로 처리:

1. recommendations.py에 한국 인기 영화 row 생성 로직 추가:
   - DB에서 한국 영화 중 weighted_score >= 6.0 필터
   - popularity DESC 정렬로 Top 100 풀 구성
   - random.sample(pool, min(50, len(pool))) 랜덤 추출
   - random.shuffle() 순서 셔플
   - korean_popular_row로 반환

2. 기존 인기 영화 row 생성 로직 (recommendations.py:264-281) 참고하여 동일 패턴 적용.
   차이점은 한국 영화 필터 조건(country = "대한민국" 또는 production_countries JSONB 포함) 추가.

3. GET /recommendations 응답의 섹션 순서에 korean_popular_row를 기존 위치에 배치:
   비로그인: 인기영화 → 한국인기영화 → 높은평점 → 날씨 → 기분 → MBTI

### 2. 프론트엔드: page.tsx에서 한국 인기 영화 직접 호출 제거

현재 page.tsx에서:
- getMovies({ country: "대한민국", sort_by: "popularity", page_size: 40 }) 별도 호출

수정:
- 이 별도 호출을 제거
- 대신 recommendations API 응답의 korean_popular_row를 사용
- 다른 섹션(인기, 높은평점, 날씨, 기분, MBTI)과 동일한 방식으로 렌더링

### 3. 중복 제거 적용

기존 deduplicate_section 로직에 korean_popular_row도 포함:
- 인기영화 → 한국인기영화 → 높은평점 순서로 seen_ids 누적
- 한국인기영화에 인기영화와 같은 영화가 나오지 않도록

## 검증
- Ctrl+F5 새로고침 3회 → 한국 인기 영화 구성과 순서가 매번 다른지
- 인기 영화 섹션과 한국 인기 영화 섹션 간 중복 없는지
- 한국 인기 영화에 실제로 한국 영화만 나오는지
- 다른 섹션(인기, 높은평점, 날씨, 기분, MBTI)은 기존대로 정상 작동

## 완료 후
- 커밋: "feat: move Korean popular movies to recommendations with random sampling"
- push 및 배포 확인
- 결과를 claude_results.md에 기록