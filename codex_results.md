# RecFlix 전체 코드 점검 및 최적화 분석 (Phase 40)

## 점검 일자
2026-02-23

## 범위
- Frontend 성능/UX/SEO
- Backend 성능/쿼리/캐시/보안
- 코드 품질(LOC, 타입, 예외 처리, 중복)

---

## Critical

1. `/movies` 장르 필터에서 `count/page` 왜곡 가능
`파일 경로:` `backend/app/api/v1/movies.py:162`, `backend/app/api/v1/movies.py:184`, `backend/app/api/v1/movies.py:194`
`현재 문제:` `join(Movie.genres)` 후 `q.count()`를 그대로 사용해 다대다 중복 카운트가 발생할 수 있고, 페이지 데이터도 중복 영화가 섞일 수 있습니다.
`개선 방안:` 장르 필터 구간에 `distinct(Movie.id)` 적용, `count(distinct(Movie.id))` 분리 쿼리로 변경, 페이지 조회도 `Movie.id` 기준 서브쿼리 후 본문 조회 2-step으로 분리.
`예상 효과:` 페이지 수/총 개수 정확도 회복, 장르 다중 선택 시 UX 오류 제거, 불필요 데이터 전송 감소.

2. 추천 API에서 N+1 가능성 높음 (응답 직렬화 시 `genres` lazy load)
`파일 경로:` `backend/app/schemas/movie.py:52`, `backend/app/api/v1/recommendations.py:178`, `backend/app/api/v1/recommendations.py:194`, `backend/app/api/v1/recommendation_engine.py:162`
`현재 문제:` `MovieListItem.from_orm_with_genres()`가 `movie.genres`를 접근하는데, 다수 쿼리에서 `selectinload(Movie.genres)`가 빠져 있어 리스트 길이만큼 추가 쿼리가 발생할 수 있습니다.
`개선 방안:` 추천/목록 반환 쿼리 공통 유틸에 `selectinload(Movie.genres)` 기본 적용, raw SQL로 ID만 뽑은 후 본 조회 시 반드시 eager load 강제.
`예상 효과:` 홈 추천/목록 API의 DB round-trip 대폭 감소, P95 응답시간 개선.

3. Refresh 토큰 재사용(Replay) 방어 부재
`파일 경로:` `backend/app/core/security.py:49`, `backend/app/core/security.py:64`, `backend/app/api/v1/auth.py:96`, `backend/app/api/v1/auth.py:100`
`현재 문제:` `/auth/refresh`는 서명/만료/타입만 검증하고, refresh 토큰 회전 기록/폐기 저장소가 없어 탈취 토큰 재사용을 막지 못합니다.
`개선 방안:` refresh 토큰에 `jti` 부여, Redis/DB 블랙리스트 또는 allowlist 도입, refresh 호출 시 이전 토큰 즉시 폐기(rotate-once) 구현.
`예상 효과:` 계정 탈취 위험도 감소, 인증 체계 보안 수준 상향.

4. 프로덕션 Rate limit 키가 프록시 환경에서 오작동 가능
`파일 경로:` `backend/app/core/rate_limit.py:8`
`현재 문제:` `get_remote_address` 단일 IP 기준이라 리버스 프록시 뒤에서 모든 사용자가 같은 IP로 묶일 수 있습니다.
`개선 방안:` `X-Forwarded-For`/`CF-Connecting-IP` 신뢰 체인 기반 key 함수로 교체하고, 인증 사용자일 때는 `user_id` 기반 제한 병행.
`예상 효과:` 정상 사용자 대량 429 방지, 공격/봇 차단 정확도 향상.

---

## Important

1. 홈 추천 1회 호출의 DB 쿼리 수가 과다
`파일 경로:` `backend/app/api/v1/recommendations.py:39`, `backend/app/api/v1/recommendations.py:130`, `backend/app/api/v1/recommendations.py:145`, `backend/app/api/v1/recommendations.py:161`
`현재 문제:` `get_home_recommendations()`는 사용자 상태에서 `get_movies_by_score` 3회 + 후보군 조회 + 선호도/유사도 조회 등으로 대략 12~20 쿼리(및 lazy 추가 쿼리) 수준입니다.
`개선 방안:` 점수 조회를 한 번의 SQL/CTE로 통합하거나, 최소한 `get_llm_movie_ids` 결과 캐시(프로세스/Redis) + `get_movies_by_score` 호출 수 축소.
`예상 효과:` 홈 진입 응답시간과 DB 부하 동시 개선.

2. `get_movies_by_score`의 동적 SQL 문자열은 안전장치가 약함
`파일 경로:` `backend/app/api/v1/recommendation_engine.py:128`
`현재 문제:` `text(f"""... {score_type} ...""")` 형태로 컬럼명이 문자열 삽입됩니다. 현재 내부 상수 호출이지만 추후 확장 시 주입 취약점 위험이 있습니다.
`개선 방안:` 허용 컬럼 whitelist 사전(`{"mbti_scores", "weather_scores", "emotion_tags"}`) 강제 검증 후 매핑된 SQL fragment만 사용.
`예상 효과:` SQL injection 류 리스크 선제 차단.

3. 검색/자동완성은 `%keyword%` 패턴으로 인덱스 효율이 낮음
`파일 경로:` `backend/app/api/v1/movies.py:71`, `backend/app/api/v1/movies.py:90`, `backend/app/api/v1/movies.py:143`
`현재 문제:` `ilike("%...%")`는 대량 데이터에서 full scan 성향이 강합니다.
`개선 방안:` PostgreSQL `pg_trgm` + GIN 인덱스 적용, 우선순위 정렬(정확 일치/접두 일치 우선)로 결과 품질 개선.
`예상 효과:` 검색 API 지연 감소, 자동완성 체감 속도 향상.

4. 온보딩 영화 추출에 `ORDER BY random()` 반복 사용
`파일 경로:` `backend/app/api/v1/movies.py:245`
`현재 문제:` 장르별 랜덤 정렬 쿼리를 반복 실행해 비용이 큽니다.
`개선 방안:` 사전 샘플 테이블/머티리얼라이즈드 뷰, 또는 해시 기반 샘플링으로 대체.
`예상 효과:` 온보딩 API 성능 안정화.

5. Weather 서비스 Redis 연결 전략 불일치
`파일 경로:` `backend/app/services/weather.py:36`, `backend/app/services/llm.py:34`
`현재 문제:` `weather.py`는 `REDIS_URL` 경로를 쓰지 않고 host/port만 사용합니다. 다른 서비스(`llm.py`)와 전략이 달라 환경별 캐시 미작동 가능성이 있습니다.
`개선 방안:` `weather.py`도 `REDIS_URL` 우선 분기 통일.
`예상 효과:` 운영 환경 캐시 hit-rate 안정화.

6. Semantic search 정규화 시 0 벡터 가드 없음
`파일 경로:` `backend/app/api/v1/semantic_search.py:66`
`현재 문제:` `query_embedding / norm`에서 norm=0인 극단 케이스 방어가 없습니다.
`개선 방안:` norm이 0이거나 매우 작은 경우 fallback 처리.
`예상 효과:` NaN 전파/비정상 결과 예방.

7. Frontend의 모든 `page.tsx`가 Client Component
`파일 경로:` `frontend/app/page.tsx:1`, `frontend/app/movies/page.tsx:1`, `frontend/app/movies/[id]/page.tsx:1`
`현재 문제:` 11개 페이지 전부 `"use client"`로 선언되어 초기 JS 전송량/수화 비용이 큽니다.
`개선 방안:` 페이지를 Server Component로 전환하고 인터랙션 컴포넌트만 client island로 분리.
`예상 효과:` LCP/TTI 개선, SEO/크롤링 안정성 향상.

8. 검색 자동완성에서 키워드/시맨틱 호출이 직렬 실행
`파일 경로:` `frontend/components/search/SearchAutocomplete.tsx:97`, `frontend/components/search/SearchAutocomplete.tsx:119`
`현재 문제:` 키워드 검색 await 완료 후 시맨틱 검색을 시작해 NL 쿼리 체감 지연이 커집니다.
`개선 방안:` `Promise.allSettled` 병렬 처리 + 최신 요청 토큰(AbortController)로 race 취소.
`예상 효과:` 검색 드롭다운 반응성 향상.

9. 이미지 최적화 비활성화
`파일 경로:` `frontend/next.config.js:9`
`현재 문제:` `images.unoptimized: true`로 Next 이미지 최적화 이점을 잃고 있습니다.
`개선 방안:` CDN 정책 확인 후 최적화 활성화, 필요 시 loader 기반 커스텀.
`예상 효과:` 이미지 전송량 감소, 모바일 성능 개선.

10. 카드 단위 Framer Motion 과다 렌더링 비용
`파일 경로:` `frontend/components/movie/MovieCard.tsx:47`, `frontend/components/movie/MovieCard.tsx:50`, `frontend/components/movie/HybridMovieCard.tsx:55`
`현재 문제:` 카드마다 `motion.div` + `delay: index * 0.05`가 누적돼 리스트가 길수록 메인 스레드 부담이 증가합니다.
`개선 방안:` 상위 컨테이너 스태거 1회 적용 또는 viewport 진입 시 1회 애니메이션으로 축소.
`예상 효과:` 스크롤/페인팅 성능 개선.

11. API 클라이언트 공통 요청 유틸의 내결함성 부족
`파일 경로:` `frontend/lib/api.ts:19`, `frontend/lib/api.ts:34`, `frontend/lib/api.ts:39`
`현재 문제:` timeout/취소/중복요청 dedupe가 없고 단순 `throw Error`만 수행합니다.
`개선 방안:` AbortController timeout, idempotent GET dedupe, 재시도 정책(429/5xx) 및 표준 에러 객체 도입.
`예상 효과:` 네트워크 불안정 구간 UX 개선, 중복 트래픽 감소.

12. 코드 규모가 큰 파일/함수가 다수
`파일 경로:` `frontend/app/movies/page.tsx`, `backend/app/api/v1/movies.py`, `frontend/components/search/SearchAutocomplete.tsx`
`현재 문제:` 파일 LOC 500+와 함수 LOC 50+가 많아 변경 리스크가 큽니다.
`개선 방안:` 도메인별 분리(쿼리/정렬/응답 변환/UI 섹션), 순수 함수 추출 + 테스트 단위 축소.
`예상 효과:` 유지보수성/리뷰 속도 향상.
`근거(파일 LOC >500):` `frontend/app/movies/page.tsx` 531, `backend/app/api/v1/movies.py` 530, `frontend/components/search/SearchAutocomplete.tsx` 522
`근거(함수 LOC >50 예시):` `backend/app/api/v1/recommendations.py:39`(191), `backend/app/api/v1/recommendation_engine.py:248`(149), `backend/app/api/v1/movies.py:320`(133), `frontend/app/movies/page.tsx:29`(476), `frontend/components/layout/Header.tsx:14`(360)

13. 타입 안정성 저하 포인트(`any`) 존재
`파일 경로:` `frontend/app/login/page.tsx:35`, `frontend/app/signup/page.tsx:55`, `frontend/components/movie/MovieCard.tsx:128`
`현재 문제:` `catch (err: any)` 및 `(x as any)`가 반복되어 타입 추론/정적 검증 이점이 약화됩니다.
`개선 방안:` `unknown` + 타입가드, `GenreLike` 유니온 타입 명시.
`예상 효과:` 런타임 타입 오류 감소.

14. 광범위 예외 처리(`except Exception`)가 많아 장애 원인 추적이 어려움
`파일 경로:` `backend/app/services/weather.py:47`, `backend/app/services/llm.py:55`, `backend/app/api/v1/movies.py:59`
`현재 문제:` 포괄 예외 후 `pass`/warn으로 흐름이 묻히는 구간이 다수 있습니다.
`개선 방안:` 외부 API/Redis/DB 예외 타입 분리, 실패 카운터/구조화 로그 필드 추가.
`예상 효과:` 장애 분석 시간 단축.

---

## Nice-to-have

1. SEO 메타데이터 적용 범위 확장 필요
`파일 경로:` `frontend/app/layout.tsx:6`, `frontend/app/movies/[id]/layout.tsx:26`
`현재 문제:` 전역/영화상세만 metadata가 있고 로그인/회원가입/마이페이지 등 개별 페이지 메타가 비어 있습니다.
`개선 방안:` 각 주요 페이지에 `export const metadata` 또는 `generateMetadata` 추가.
`예상 효과:` 검색 유입 및 공유 미리보기 품질 개선.

2. Route-level `loading.tsx` 부재
`파일 경로:` `frontend/app` (route loading 파일 없음)
`현재 문제:` Suspense fallback은 있으나 라우트 표준 로딩 경로가 부족합니다.
`개선 방안:` `/`, `/movies`, `/movies/[id]` 중심으로 `loading.tsx` 추가.
`예상 효과:` 라우팅 전환 체감 개선.

3. 접근성: 확대 제한
`파일 경로:` `frontend/app/layout.tsx:46`, `frontend/app/layout.tsx:47`
`현재 문제:` `maximumScale: 1`, `userScalable: false`로 저시력 사용자 접근성을 제한합니다.
`개선 방안:` 확대 제한 제거.
`예상 효과:` 접근성 준수 수준 향상.

4. 홈 캐시 키가 사용자 식별자를 포함하지 않음
`파일 경로:` `frontend/app/page.tsx:104`, `frontend/app/page.tsx:131`
`현재 문제:` 캐시 키가 `weather/mood/isAuthenticated`만 포함해 사용자 맥락 변화를 충분히 반영하지 못할 수 있습니다.
`개선 방안:` `user.id`, `user.mbti`, `preferred_genres` 해시 포함.
`예상 효과:` 개인화 결과 일관성 개선.

5. 빌드/타입/스타일 부채 추적 필요
`파일 경로:` `backend/app` 전반
`현재 문제:` `ruff check` 기준 143건(주로 타입 표기/import 정렬/예외 스타일) 누적.
`개선 방안:` 린트 규칙 단계적 엄격화(경고->오류), 자동수정 가능한 항목부터 일괄 정리.
`예상 효과:` 코드 일관성 및 신규 코드 품질 개선.

---

## 리팩토링 Phase 제안 (우선순위 순)

1. **Phase 1 (안전/정확성)**
- `/movies` 장르 필터 `distinct` 정합성 수정
- Refresh 토큰 회전/폐기 저장소 도입
- 프록시 인식 Rate limit key 적용

2. **Phase 2 (DB 성능)**
- 추천 API eager loading/N+1 제거
- `get_home_recommendations` 쿼리 통합 및 호출 수 축소
- 검색 인덱스(pg_trgm + GIN) 적용

3. **Phase 3 (Frontend 체감 성능)**
- `movies/page`, `SearchAutocomplete` 분할
- 검색 병렬 요청 + 취소(AbortController)
- 카드 애니메이션 경량화

4. **Phase 4 (아키텍처/SEO)**
- 페이지 Server Component 전환(선별)
- route metadata/loading 정비
- API 클라이언트 공통 에러/재시도 표준화

5. **Phase 5 (품질 자동화)**
- lint/type 기준 강화(`any` 감축, broad except 축소)
- CI에서 성능 회귀 체크(쿼리 수, 응답시간) 추가

---

## 실행 로그 요약
- `python -m compileall backend/app`: 통과 (문법 오류 없음)
- `cmd /c npm run lint` (frontend): 통과 (`No ESLint warnings or errors`)
- `python -m ruff check backend/app`: 143건(대부분 스타일/타입 표기 부채)
