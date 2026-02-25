# RecFlix 기술 의사결정 기록 (ADR)

**최종 업데이트**: 2026-02-25

---

## 2026-02-24: sync → async 블로킹 해소 전략 (Phase 48)

- **문제**: async 라우트에서 bcrypt 해싱, httpx 동기 호출이 이벤트 루프를 블로킹
- **대안**:
  - A) 전체 동기(sync) 라우트로 전환
  - B) 블로킹 부분만 `asyncio.to_thread` 래핑
  - C) 완전한 async stack (async bcrypt, async httpx)
- **결정**: B) `bcrypt`를 `to_thread`로 래핑 + httpx `AsyncClient` 싱글톤
- **근거**: 현재 트래픽 규모에서 충분, 최소 변경으로 블로킹 해소. 전체 async 전환은 overkill.
- **파일**: `backend/app/core/security.py`, `backend/app/core/http_client.py`

---

## 2026-02-24: 시맨틱 재랭킹 v2 (Phase 49)

- **문제**: 시맨틱 검색에서 popularity 가중치 30%로 블록버스터가 결과 과점
- **대안**:
  - A) popularity 비중 감소 (30% → 15%)
  - B) popularity에 log 스케일 적용
  - C) 둘 다 적용
- **결정**: C) 0.30 → 0.15 + log 스케일
- **근거**: 인디 영화 노출 증가, 검색 의도 반영 강화. A/B 테스트로 검증 가능.
- **파일**: `backend/app/api/v1/semantic_search.py`

---

## 2026-02-24: SQLite in-memory 테스트 (Phase 49)

- **문제**: CI/CD에서 PostgreSQL 서비스 없이 테스트 필요
- **대안**:
  - A) GitHub Actions에 PostgreSQL 서비스 추가
  - B) SQLite in-memory로 기본 테스트
  - C) testcontainers 사용
- **결정**: B) SQLite in-memory + PostgreSQL 전용 기능(JSONB, pg_trgm)은 스킵
- **근거**: CI 속도 우선, JSONB 테스트는 향후 PostgreSQL CI로 분리 예정
- **파일**: `backend/tests/conftest.py`

---

## 2026-02-24: CF item_bias 유지 결정 (Phase 49)

- **문제**: SVD 모델에서 user-level CF 불가 (RecFlix 사용자가 MovieLens에 없음)
- **대안**:
  - A) item_bias만 사용 (현재)
  - B) RecFlix 평점으로 자체 CF 학습
  - C) CF 모듈 제거
- **결정**: A) item_bias 유지 + A/B 테스트로 CF 가중치별 효과 측정
- **근거**: 사용자 데이터 축적 중. 충분한 데이터 확보 후 B로 전환 계획.
- **파일**: `backend/app/api/v1/recommendation_cf.py`

---

## 2026-02-23: Alembic 도입, create_all 제거 (Phase 48)

- **문제**: `Base.metadata.create_all()`로 스키마 관리 → 프로덕션에서 마이그레이션 불가
- **대안**:
  - A) create_all 유지 + 수동 ALTER TABLE
  - B) Alembic 마이그레이션 도입
- **결정**: B) Alembic 도입, `create_all` 제거
- **근거**: 프로덕션 DB 스키마 변경 이력 추적 필수. 롤백 가능.
- **파일**: `backend/alembic/`, `backend/app/database.py`

---

## 2026-02-23: 트레일러 Trailer 타입만 수집 (Phase 47)

- **문제**: TMDB API에서 Trailer, Teaser, Clip, Featurette 등 다양한 비디오 타입 제공
- **대안**:
  - A) 모든 비디오 타입 수집
  - B) Trailer만 수집 (공식 예고편)
  - C) Trailer + Teaser 수집
- **결정**: B) Trailer 타입, YouTube 소스만 수집
- **근거**: 공식 예고편이 사용자에게 가장 유용. Teaser는 정보량 부족. 28,486편 수집 완료.
- **파일**: `backend/scripts/collect_trailers.py`, `backend/app/models/movie.py`

---

## 2026-02-23: localStorage 토큰 유지 (Phase 46)

- **문제**: JWT를 localStorage에 저장 → XSS 취약점 우려
- **대안**:
  - A) HttpOnly 쿠키 전환
  - B) localStorage 유지 + CSP 강화
  - C) 메모리 기반 + refresh token 쿠키
- **결정**: B) localStorage 유지 + 보안 헤더 강화
- **근거**: 쿠키 전환은 CORS/SSR 구조 대폭 변경 필요. 현재 규모에서 CSP로 충분. 향후 트래픽 증가 시 A 검토.
- **파일**: `frontend/stores/authStore.ts`, `backend/app/core/security.py`

---

## 2026-02-23: 추천 콜드스타트 preferred_genres 폴백 (Phase 46)

- **문제**: 신규 사용자(찜/평점 < 5건)의 personal_score가 0에 가까움
- **대안**:
  - A) 온보딩 선호 장르로 genre_counts 초기화
  - B) 인기 영화 기반 기본 추천
  - C) 둘 다
- **결정**: A) `preferred_genres` JSON에서 장르 매핑 후 genre_counts에 1점 추가
- **근거**: 최소 개인화 시그널 제공. 향후 가중치 상향 검토.
- **파일**: `backend/app/api/v1/recommendation_engine.py:248-261`

---

## 2026-02-20: 추천 다양성 정책 5중 파이프라인 (Phase 34)

- **문제**: 추천 결과가 특정 장르(드라마, 스릴러)에 편중
- **대안**:
  - A) 단순 장르 셔플
  - B) 다중 다양성 정책 파이프라인
- **결정**: B) 5단계 파이프라인 — 장르 캡(35%) → 장르 연속 제한(3편) → 신선도(최신 20%, 클래식 10%) → 세렌디피티(10%) → 섹션 중복 제거
- **근거**: 단일 정책으로는 해결 불가. 각 정책이 독립적으로 작동하여 조합 효과.
- **파일**: `backend/app/api/v1/diversity.py`, `recommendation_constants.py`
