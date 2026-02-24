codex --reasoning high "RecFlix 추천 알고리즘 + 웹서비스 프로덕션 수준 점검.

현재 Phase 45까지 완료된 상태. 실제 서비스 런칭 관점에서 부족한 점을 빠짐없이 분석.

=== A. 추천 알고리즘 점검 ===

1. 추천 품질 분석:
   - backend/app/api/v1/recommendation_engine.py 읽고 하이브리드 스코어링 흐름 분석
   - backend/app/api/v1/recommendation_constants.py 가중치 체계 적절성
   - backend/app/api/v1/recommendation_cf.py SVD 활용 방식 분석
   - backend/app/api/v1/diversity.py 다양성 정책의 실효성
   - backend/app/api/v1/recommendation_reason.py 추천 이유 자연스러움
   - 콜드스타트 문제: 신규 사용자(평점 0, MBTI만)에게 추천 품질은?
   - 인기 편향: weighted_score >= 6.0 필터가 롱테일 영화를 얼마나 차단하는지
   - 시간 경과 효과: 사용자 취향 변화를 반영하는 메커니즘이 있는지
   - 피드백 루프: 평점/찜이 실시간으로 추천에 반영되는지, 아니면 다음 세션?

2. 시맨틱 검색 품질:
   - backend/app/api/v1/semantic_search.py 재랭킹 공식 적절성
   - 한국어 쿼리 처리 품질 (Voyage AI multilingual 한계)
   - 검색 결과 다양성 vs 정확도 밸런스

3. 추천 데이터 파이프라인:
   - emotion_tags 2-Tier (LLM 1,711 vs 키워드 41,206)의 품질 격차 영향
   - mbti_scores/weather_scores 생성 로직이 어디에 있는지, 갱신 주기
   - similar_movies 429,170 관계의 신선도 (새 영화 추가 시 갱신 방법)

=== B. 웹서비스 프로덕션 수준 점검 ===

4. 성능/스케일링:
   - 현재 동시 접속 처리 능력 추정 (Railway 스펙 기준)
   - 임베딩 42,917 x 1024 인메모리 로드의 메모리 사용량
   - Redis 캐시 전략 종합 점검 (TTL, 키 설계, 히트율 추정)
   - DB 커넥션 풀 설정 확인 (backend/app/database.py)

5. 에러 핸들링/모니터링:
   - Sentry 설정 상태 확인 (backend/app/main.py)
   - 에러 발생 시 사용자 경험 (프론트엔드 에러 바운더리)
   - 헬스체크 커버리지 (backend/app/api/v1/health.py)
   - 로깅 구조화 수준 (structured logging? JSON?)

6. 사용자 경험:
   - 첫 방문 → 추천까지의 UX 흐름 점검
   - 로그인/비로그인 추천 차이
   - 모바일 UX 완성도
   - 페이지 전환 속도 체감
   - 에러 상태 UI 커버리지

7. 데이터 관리:
   - 영화 데이터 갱신 파이프라인 (TMDB 신작 반영 방법)
   - 사용자 데이터 백업/복구 전략
   - GDPR/개인정보 처리 (회원 탈퇴, 데이터 삭제)

8. 인프라/배포:
   - Railway 단일 인스턴스 장애 시 복구 전략
   - 환경별 분리 (staging/production)
   - DB 마이그레이션 자동화 (현재 수동 SQL)
   - 시크릿 관리 현황

=== 출력 형식 ===

카테고리별로:
- 🔴 Must-have (서비스 런칭 전 필수)
- 🟡 Should-have (런칭 후 빠르게)
- 🟢 Nice-to-have (점진적 개선)

각 항목마다:
- 현재 상태
- 문제/리스크
- 개선 방안
- 예상 난이도 (Low/Medium/High)
- 예상 소요 (Phase 단위)

마지막에 추천 로드맵 (Phase 순서) 제안.

결과를 codex_results.md에 덮어쓰기."