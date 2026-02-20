claude "Phase 34: 추천 다양성/신선도 정책 구현.

=== Research ===
먼저 다음 파일들을 읽고 현재 구조를 파악할 것:
- CLAUDE.md
- backend/app/api/v1/recommendation_engine.py (전체)
- backend/app/api/v1/recommendations.py (전체)
- backend/app/api/v1/recommendation_constants.py (전체)
- backend/app/api/v1/movies.py (semantic-search 엔드포인트)
- backend/app/models/movie.py (Movie 모델, genres 관계)

=== 1단계: diversity.py 생성 ===
backend/app/api/v1/diversity.py 신규 생성. 4개 함수:

1. diversify_by_genre(scored_movies, limit, max_consecutive=3)
   - 같은 primary genre가 max_consecutive개 연속 불가
   - genre_window로 최근 장르 추적
   - 조건 불만족 시 제약 완화 후 최고점 선택 (graceful)
   - 입력/출력: [(movie, score, tags)] 형식 유지

2. apply_genre_cap(scored_movies, limit, max_genre_ratio=0.35)
   - 단일 장르가 전체의 35% 초과 불가
   - 5편 이하일 때는 제한 없음
   - 부족하면 스킵된 영화로 채움

3. ensure_freshness(scored_movies, limit, recent_years=3, classic_years=10, recent_ratio=0.20, classic_ratio=0.10)
   - 최신작(3년 이내) 최소 20%, 클래식(10년+) 최소 10% 보장
   - 나머지는 스코어 순 채움
   - release_date 없는 영화는 middle로 분류

4. inject_serendipity(scored_movies, limit, user_top_genres, db, serendipity_ratio=0.10, min_quality=7.0)
   - 추천 리스트의 10%를 사용자 선호 장르 외의 고품질 영화로
   - DB에서 랜덤 선택 (func.random())
   - 리스트 70% 지점에 삽입
   - 태그: RecommendationTag(type='serendipity', label='#의외의발견', score=0.0)
   - user_top_genres가 비어있으면 스킵

모든 함수는 입력이 부족하거나 빈 리스트일 때 원본 그대로 반환 (안전).

=== 2단계: recommendation_constants.py 수정 ===
다양성 설정 상수 추가:
DIVERSITY_ENABLED = True
GENRE_MAX_CONSECUTIVE = 3
GENRE_MAX_RATIO = 0.35
FRESHNESS_RECENT_RATIO = 0.20
FRESHNESS_CLASSIC_RATIO = 0.10
SERENDIPITY_RATIO = 0.10
SERENDIPITY_MIN_QUALITY = 7.0
SEMANTIC_GENRE_MAX = 5

=== 3단계: recommendation_engine.py 수정 ===
calculate_hybrid_scores() 함수의 최종 정렬 후, 리턴 전에 다양성 파이프라인 적용:
```python
from .diversity import diversify_by_genre, apply_genre_cap, ensure_freshness
from .recommendation_constants import DIVERSITY_ENABLED, GENRE_MAX_CONSECUTIVE, GENRE_MAX_RATIO, FRESHNESS_RECENT_RATIO, FRESHNESS_CLASSIC_RATIO

# 기존 스코어 계산 + 정렬 (변경 없음)
# ...

# 다양성 후처리 (기존 로직 다음에 추가)
if DIVERSITY_ENABLED:
    scored = apply_genre_cap(scored, pool_size, GENRE_MAX_RATIO)
    scored = diversify_by_genre(scored, pool_size, GENRE_MAX_CONSECUTIVE)
    scored = ensure_freshness(scored, pool_size, recent_ratio=FRESHNESS_RECENT_RATIO, classic_ratio=FRESHNESS_CLASSIC_RATIO)
```

⚠️ calculate_hybrid_scores의 실제 반환 형식을 먼저 확인하고 그에 맞게 적용할 것.
⚠️ scored_movies가 [(movie, score, tags)] 형식이 아닐 수 있음 — 실제 형식에 맞게 diversity.py 함수 시그니처 조정.

=== 4단계: recommendations.py 수정 ===
홈 추천 엔드포인트에서 섹션 간 중복 제거:
- seen_ids: set[int] = set()
- 각 섹션 빌드 후 seen_ids에 추가
- 다음 섹션에서 seen_ids에 있는 영화 제외
- 우선순위: hybrid > MBTI > 날씨 > 기분 > 인기 > 높은평점

for-you 엔드포인트에 serendipity 적용:
- 사용자 찜/평점에서 top_genres 추출
- inject_serendipity() 호출

=== 5단계: movies.py 시맨틱 검색 다양성 ===
semantic-search 엔드포인트의 재랭킹 후에 장르 다양성 적용:
- 같은 장르 최대 5편 (SEMANTIC_GENRE_MAX)
- diversify_by_genre 또는 별도 간단 함수 사용

=== 규칙 ===
- calculate_hybrid_scores의 스코어 계산 로직 자체는 수정 금지
- 가중치(WEIGHTS 딕셔너리 등) 수정 금지
- 다양성은 스코어 계산 '후'에 후처리로만 적용
- DIVERSITY_ENABLED = False로 즉시 비활성화 가능해야 함
- 기존 weighted_score >= 6.0 품질 필터 유지
- popular, top-rated 섹션에는 다양성 미적용
- 모든 함수에 타입 힌트 + docstring
- 모든 .md 문서 파일 건드리지 말 것

=== 검증 ===
1. cd backend && ruff check app/api/v1/diversity.py
2. cd backend && python -c 'from app.api.v1.diversity import diversify_by_genre, apply_genre_cap, ensure_freshness, inject_serendipity; print(\"import OK\")'
3. 로컬 서버 시작 후 다양성 전/후 비교:
   curl 'http://localhost:8000/api/v1/recommendations/for-you?weather=rainy&mood=calm&mbti=INTJ&limit=20'
   → Top 3 장르 집중도가 62.9% → 55% 이하로 감소 확인
   → 같은 장르 3개 연속 없는지 확인
4. 시맨틱 검색 다양성:
   curl 'http://localhost:8000/api/v1/movies/semantic-search?q=비오는+날+좋은+영화&limit=20'
   → 같은 장르 5편 초과 없는지 확인
5. cd backend && ruff check app/api/v1/
6. git add -A && git commit -m 'feat: Phase 34 추천 다양성/신선도 정책 (장르 다양성 + 신선도 + serendipity + 중복 제거)' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- diversity.py 함수 목록
- 다양성 전/후 비교 (장르 분포, 연도 분포)
- 적용된 엔드포인트 매트릭스
- 프로덕션 재배포 필요 여부"