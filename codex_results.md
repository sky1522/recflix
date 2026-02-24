# RecFlix 추천 알고리즘 + 웹서비스 프로덕션 점검 (Phase 45 기준)

작성일: 2026-02-23  
분석 범위: 추천 엔진/검색/데이터 파이프라인/운영·배포·보안/UX

---

## 🔴 Must-have (런칭 전 필수)

### [A-1] "LLM 30% 보장"의 기준 데이터 정합성 보강
- 현재 상태: LLM 영화를 `vote_count >= 50` 상위 1,000편으로 간주해 섞고 있음.  
  근거: `backend/app/api/v1/recommendation_engine.py:98`, `backend/app/api/v1/recommendation_engine.py:170`
- 문제/리스크: 실제 LLM 분석 여부와 무관한 영화가 포함될 수 있어 품질 가정이 깨질 수 있음.
- 개선 방안: `emotion_source`(llm/keyword) 또는 `is_llm`을 DB에 명시하고, 보장 로직을 해당 필드 기반으로 변경.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [A-2] 온보딩 선호 장르가 추천 계산에 직접 반영되지 않음
- 현재 상태: `preferred_genres`를 저장하지만 추천 스코어 계산에서는 사용하지 않음.  
  근거: `backend/app/api/v1/users.py:71`, `backend/app/api/v1/recommendation_engine.py:201`
- 문제/리스크: 신규 사용자 콜드스타트에서 추천 정밀도가 빠르게 올라가지 않음.
- 개선 방안: 평점/찜 데이터가 적은 구간에서 `preferred_genres`를 personal prior로 반영.
- 예상 난이도: Low
- 예상 소요: 0.5 Phase

### [A-3] 피드백 루프 체감 지연 (프론트 추천 캐시 키 설계)
- 현재 상태: 추천 캐시 키가 `weather/mood/user/mbti` 중심이며 평점·찜 변경은 반영되지 않음.  
  근거: `frontend/app/page.tsx:37`, `frontend/app/page.tsx:104`
- 문제/리스크: 사용자가 방금 평점/찜을 바꿔도 홈 추천이 즉시 갱신되지 않는 UX 발생.
- 개선 방안: 평점/찜 mutate 시 캐시 무효화 또는 `interaction_version` 키 도입.
- 예상 난이도: Low
- 예상 소요: 0.5 Phase

### [A-4] `weighted_score >= 6.0` 고정 하한으로 롱테일 노출 제한
- 현재 상태: 추천 주요 경로에서 6.0 하한이 고정으로 적용됨.  
  근거: `backend/app/api/v1/recommendation_engine.py:123`, `backend/app/api/v1/recommendations.py:65`
- 문제/리스크: 비주류·신규·취향 특화 콘텐츠 노출이 줄어 탐색 다양성 저하.
- 개선 방안: 사용자군별 동적 하한(예: 5.2~6.5), 세렌디피티 슬롯 확대, A/B 검증.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-1] async 엔드포인트 내부 블로킹 I/O/CPU 처리
- 현재 상태: async 라우트에서 동기 HTTP/DB 또는 고비용 연산이 섞여 있음.  
  근거: `backend/app/api/v1/auth.py:187`, `backend/app/api/v1/movies.py:327`
- 문제/리스크: 이벤트 루프 블로킹으로 동시성 하락, 피크 타임 지연/타임아웃 위험.
- 개선 방안: sync 라우트로 통일해 threadpool 사용 또는 async stack(SQLAlchemy async + AsyncClient)으로 일관 전환.
- 예상 난이도: High
- 예상 소요: 1.5 Phase

### [B-2] 런타임 `create_all` + 수동 SQL 마이그레이션 구조
- 현재 상태: 앱 시작 시 `Base.metadata.create_all` 실행, Alembic 체계 없음.  
  근거: `backend/app/main.py:42`, `backend/scripts/migrate_add_columns.py`
- 문제/리스크: 스키마 drift, 배포 순서 의존, 롤백 난이도 상승.
- 개선 방안: Alembic 도입, 배포 단계에서 migrate 강제, 런타임 DDL 제거.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-3] Rate limit 신뢰 경계 취약
- 현재 상태: `TRUSTED_PROXIES` 미설정 시 전달 헤더를 사실상 신뢰함.  
  근거: `backend/app/core/rate_limit.py:20`
- 문제/리스크: 헤더 스푸핑으로 IP 기반 제한 우회 가능.
- 개선 방안: 운영 프록시 CIDR 필수 설정, 미설정 시 XFF 무시가 기본이 되도록 반전.
- 예상 난이도: Low
- 예상 소요: 0.5 Phase

### [B-4] 인증 토큰 localStorage 저장
- 현재 상태: access/refresh 토큰을 localStorage에 저장.  
  근거: `frontend/stores/authStore.ts:31`, `frontend/stores/authStore.ts:55`
- 문제/리스크: XSS 발생 시 토큰 탈취 위험.
- 개선 방안: HttpOnly/Secure/SameSite 쿠키 기반 전환 + CSRF 방어.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-5] 빌드 시 외부 대용량 파일 직접 다운로드
- 현재 상태: Docker build 중 GitHub URL에서 모델/임베딩 직접 curl.  
  근거: `backend/Dockerfile:28`
- 문제/리스크: 재현성/공급망/가용성 리스크, 빌드 실패 시 배포 불안정.
- 개선 방안: 버전 고정 아티팩트 저장소(S3/Release) + 체크섬 검증 + fallback.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

---

## 🟡 Should-have (런칭 후 빠른 보강)

### [A-5] CF가 실사용자 협업필터링보다 품질 prior에 가까움
- 현재 상태: `global_mean + item_bias` 형태로 사용자별 협업 신호가 약함.  
  근거: `backend/app/api/v1/recommendation_cf.py:7`, `backend/app/api/v1/recommendation_cf.py:63`
- 문제/리스크: 개인화 분리도 부족, 장기적으로 추천 차별성 약화.
- 개선 방안: RecFlix 이벤트/평점 기반 implicit CF(ALS/BPR) 또는 retrieval 모델 도입.
- 예상 난이도: High
- 예상 소요: 1.5 Phase

### [A-6] 시간 경과 반영 로직 제한적
- 현재 상태: 최근 90일 고평점 중심 가중만 존재.  
  근거: `backend/app/api/v1/recommendation_engine.py:226`
- 문제/리스크: 취향 변화 반영 속도 느림.
- 개선 방안: 이벤트/평점 time-decay, 세션 단기 컨텍스트 가중치 추가.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [A-7] 추천 이유 문구의 반복성
- 현재 상태: 템플릿 기반 문구 생성으로 저비용/저지연 구조.  
  근거: `backend/app/api/v1/recommendation_reason.py:1`
- 문제/리스크: 문구 반복으로 설명 신뢰도 저하.
- 개선 방안: 기여도 상위 feature 노출, 템플릿 다양화, 품질 A/B 테스트.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

### [A-8] 시맨틱 검색 재랭킹의 인기 편향
- 현재 상태: `semantic 0.50 + popularity 0.30 + quality 0.20`.  
  근거: `backend/app/api/v1/movies.py:269`
- 문제/리스크: 질의 의도보다 대중성이 상단을 과점할 가능성.
- 개선 방안: 질의 타입별 동적 가중치, 오프라인 NDCG 기반 튜닝.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

### [A-9] 한국어 질의 전처리 부재
- 현재 상태: 임베딩 전 형태소/동의어/오탈자 정규화 파이프라인 미확인.  
  근거: `backend/app/services/embedding.py:66`
- 문제/리스크: 한국어 구어체/축약어 검색 품질 저하.
- 개선 방안: 질의 정규화 + 동의어 확장 사전 + fallback keyword 강화.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-6] 홈 추천 응답 페이로드 과대
- 현재 상태: 섹션당 최대 50개, hybrid 40개를 한 번에 전달.  
  근거: `backend/app/api/v1/recommendations.py:77`, `backend/app/api/v1/recommendations.py:130`
- 문제/리스크: 모바일 초기 로딩 및 체감 속도 저하.
- 개선 방안: 1차 응답 축소(10~20개) + 섹션별 lazy fetch/pagination.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

### [B-7] 관측성(로그 구조화/SLO/알람) 고도화 필요
- 현재 상태: Sentry는 연결되어 있으나 로그는 plain text 위주.  
  근거: `backend/app/main.py:18`, `backend/app/main.py:29`
- 문제/리스크: 장애 탐지/원인분석(RCA) 속도 저하.
- 개선 방안: JSON 로그, request-id 상관관계, 5xx/latency/error budget 알람.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

### [B-8] 테스트 게이트 부족
- 현재 상태: CI는 lint/build 중심, 타입체크는 non-blocking.  
  근거: `.github/workflows/ci.yml:31`, `.github/workflows/ci.yml:74`
- 문제/리스크: 회귀가 main 배포로 직행할 위험.
- 개선 방안: 핵심 API contract test + 추천 스모크 테스트를 필수 게이트로 추가.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-9] 데이터 갱신 파이프라인 자동화 부족
- 현재 상태: 점수/태그/유사도 계산이 스크립트 수동 실행 중심.  
  근거: `backend/scripts/llm_emotion_tags.py`, `backend/scripts/compute_similar_movies.py`
- 문제/리스크: 신작 반영 지연, 운영자 의존 증가.
- 개선 방안: 주기 실행(cron/worker) + 실패 재시도 + 실행 상태 대시보드.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-10] GDPR/탈퇴 삭제 플로우 미비
- 현재 상태: `/users/me` 조회/수정만 존재, 탈퇴·완전삭제 엔드포인트 없음.  
  근거: `backend/app/api/v1/users.py:17`
- 문제/리스크: 개인정보 삭제 요청 대응 어려움.
- 개선 방안: `/users/me` DELETE + 연관 데이터 삭제/익명화 정책 + 감사로그.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

---

## 🟢 Nice-to-have (점진 개선)

### [A-10] 컨텍스트 밴딧 기반 온라인 최적화
- 현재 상태: 정적 가중치 + A/B 분기 중심.
- 문제/리스크: 사용자별 최적 조합 탐색 속도 제한.
- 개선 방안: CTR/완주율 보상 기반 contextual bandit 적용.
- 예상 난이도: High
- 예상 소요: 1.5 Phase

### [A-11] 추천 품질 대시보드 고도화
- 현재 상태: 이벤트 통계/AB 리포트 API 제공.
- 문제/리스크: 오프라인 지표(NDCG/Coverage/Novelty) 연계 부족.
- 개선 방안: 오프라인 평가 파이프라인 + 온라인 KPI 통합 대시보드.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

### [B-11] Backend staging 환경 분리
- 현재 상태: main → production 중심 배포.
- 문제/리스크: 사전 검증 환경 부족.
- 개선 방안: staging 서비스/DB 분리 + promote 방식 배포.
- 예상 난이도: Medium
- 예상 소요: 0.5 Phase

### [B-12] 검색 인덱스/쿼리 플랜 운영 자동화
- 현재 상태: 일부 인덱스 생성이 수동 SQL 스크립트 중심.  
  근거: `backend/scripts/migrate_search_index.sql`
- 문제/리스크: 환경별 인덱스 불일치 가능성.
- 개선 방안: 마이그레이션 체계 편입 + 쿼리 플랜 회귀 점검 자동화.
- 예상 난이도: Low
- 예상 소요: 0.5 Phase

---

## 추천 로드맵 (Phase 순서)

### Phase 46 — 런칭 차단 이슈 해소
- [B-1] async 블로킹 제거
- [B-2] Alembic 전환
- [B-3] Trusted proxy 강제
- [B-4] 토큰 저장 방식 개선 착수
- [B-5] 아티팩트 공급망 고정

### Phase 47 — 추천 품질 핵심 보정
- [A-1] LLM 소스 판별 정확화
- [A-2] 온보딩 선호 반영
- [A-3] 피드백 루프 실시간화
- [A-4] 롱테일 노출 조정

### Phase 48 — 운영성 강화
- [B-6] 응답 페이로드 경량화
- [B-7] 구조화 로그/SLO/알람
- [B-8] 테스트 게이트 강화
- [B-10] GDPR/탈퇴 처리

### Phase 49 — 데이터/모델 고도화
- [A-5] CF v2
- [A-6] 시간 감쇠 반영
- [A-8] 재랭킹 튜닝
- [A-9] 한국어 검색 전처리
- [B-9] 배치 자동화

### Phase 50+ — 성장 최적화
- [A-10] 온라인 최적화(밴딧)
- [A-11] 통합 품질 대시보드
- [B-11], [B-12] 환경/인덱스 운영 고도화

---

## 총평
현재 구조는 “서비스 동작” 수준은 충족하지만, 런칭 안정성과 추천 신뢰도를 함께 확보하려면 **동시성/보안/데이터 정합성(🔴)** 항목을 먼저 닫는 것이 필수입니다. 이후 1~2개 Phase 내에 추천 품질과 운영 자동화를 보강하면, 트래픽 증가에도 안정적으로 확장 가능한 구조로 갈 수 있습니다.
