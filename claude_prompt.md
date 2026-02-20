claude "Phase 33-5: 시맨틱 검색 품질 개선 — 재랭킹 + 인기도 반영.

=== Research ===
먼저 다음 파일들을 읽고 현재 로직을 파악할 것:
- backend/app/api/v1/movies.py (semantic-search 엔드포인트 전체)
- backend/app/api/v1/semantic_search.py (search_similar 함수)
- backend/app/api/v1/recommendation_engine.py (기존 하이브리드 스코어링 참고)
- backend/app/models/movie.py (weighted_score, vote_count 등 필드)

그리고 현재 문제를 확인:
- curl 'https://backend-production-cff2.up.railway.app/api/v1/movies/semantic-search?q=비오는+날+혼자+보기+좋은+잔잔한+영화&limit=10'
- curl 'https://backend-production-cff2.up.railway.app/api/v1/movies/semantic-search?q=감동적인+가족+영화+추천&limit=10'
- curl 'https://backend-production-cff2.up.railway.app/api/v1/movies/semantic-search?q=스릴+넘치는+반전+영화&limit=10'
결과에서 무명 영화가 상위에 오고, 쇼생크 탈출/인셉션/인터스텔라 같은 명작이 안 나오는지 확인.

=== 문제 분석 ===
현재 시맨틱 검색이 semantic_score(벡터 유사도)만으로 정렬하면:
- 제목이나 줄거리에 '비', '혼자', '잔잔' 같은 단어가 직접 들어간 무명 영화가 상위
- 실제로 분위기가 맞지만 다른 표현을 쓰는 명작은 하위

사용자가 기대하는 건: 분위기가 맞으면서 + 잘 알려진 + 평점 높은 영화

=== 수정 사항: 재랭킹 공식 개선 ===

현재: semantic_score만으로 정렬 (또는 단순 필터)
변경: 복합 점수로 재랭킹
```python
# 최종 점수 = semantic_score * 0.5 + popularity_score * 0.3 + quality_score * 0.2

def calculate_relevance_score(semantic_score: float, movie: Movie) -> float:
    # 1. semantic_score (0~1): 벡터 유사도 — 이미 있음
    
    # 2. popularity_score (0~1): 인기도 (로그 스케일)
    #    vote_count가 높을수록 많은 사람이 본 영화
    #    log 스케일로 정규화 (vote_count 0~50000 → 0~1)
    import math
    vote_count = movie.vote_count or 0
    popularity_score = min(math.log1p(vote_count) / math.log1p(50000), 1.0)
    
    # 3. quality_score (0~1): 평점 품질
    #    weighted_score를 0~10 → 0~1로 정규화
    weighted_score = movie.weighted_score or 0
    quality_score = min(max(weighted_score / 10.0, 0), 1.0)
    
    # 4. 최종 복합 점수
    relevance = (
        semantic_score * 0.50 +
        popularity_score * 0.30 +
        quality_score * 0.20
    )
    return relevance
```

=== 적용 위치 ===
backend/app/api/v1/movies.py의 semantic-search 엔드포인트에서:
1. search_similar()로 Top 100 후보 추출 (기존)
2. DB에서 후보 영화 조회 (기존)
3. ★ 각 영화에 calculate_relevance_score 적용
4. ★ relevance_score 기준으로 재정렬
5. 상위 limit개 반환

=== 추가 개선: weighted_score 필터 완화 ===
현재 weighted_score >= 5.0 또는 6.0 필터가 있으면:
- >= 5.0으로 완화 (너무 높으면 후보가 줄어듦)
- 단, relevance_score 재랭킹으로 저품질은 자연스럽게 하위로 밀림

=== 응답에 match_reason 추가 ===
각 결과에 왜 이 영화가 추천됐는지 간단한 이유 태그:
```python
def get_match_reason(semantic_score: float, popularity_score: float, quality_score: float) -> str:
    reasons = []
    if semantic_score >= 0.45:
        reasons.append("분위기 일치")
    if quality_score >= 0.75:
        reasons.append("높은 평점")
    if popularity_score >= 0.5:
        reasons.append("많은 관객")
    if not reasons:
        reasons.append("AI 추천")
    return " · ".join(reasons)
```

=== 규칙 ===
- semantic_search.py의 search_similar 함수 수정 금지 (벡터 검색 자체는 정상)
- 기존 추천 엔진(recommendation_engine.py) 수정 금지
- movies.py의 기존 키워드 검색 엔드포인트 수정 금지
- 시맨틱 검색 엔드포인트 내부 재랭킹 로직만 수정

=== 검증 ===
1. 로컬 서버 재시작 후 테스트:
   curl 'http://localhost:8000/api/v1/movies/semantic-search?q=비오는+날+혼자+보기+좋은+잔잔한+영화&limit=10'
   → 쇼생크 탈출, 어바웃 타임, 굿 윌 헌팅 등 명작이 상위 5위 안에 있어야 함

2. curl 'http://localhost:8000/api/v1/movies/semantic-search?q=스릴+넘치는+반전+영화&limit=10'
   → 인셉션, 올드보이, 파이트 클럽 등 유명 스릴러가 상위에 있어야 함

3. curl 'http://localhost:8000/api/v1/movies/semantic-search?q=감동적인+가족+영화+추천&limit=10'
   → 인생은 아름다워, 코코, 소울 등이 상위에 있어야 함

4. 응답에 match_reason 필드 포함 확인

5. cd backend && ruff check app/api/v1/movies.py

6. git add -A && git commit -m 'feat: 시맨틱 검색 재랭킹 개선 (인기도+품질 복합점수 + match_reason)' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 수정 전/후 검색 결과 비교 (3개 쿼리)
- 재랭킹 공식 설명
- match_reason 예시
- 프로덕션 재배포 필요 여부"