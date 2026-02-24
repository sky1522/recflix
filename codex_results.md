# RecFlix 추천 알고리즘 + 웹서비스 프로덕션 점검 (Phase 45 기준, Phase 50 해결 반영)

작성일: 2026-02-23 (Phase 46~50 해결 사항 반영: 2026-02-24)
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

### [A-2] ~~온보딩 선호 장르가 추천 계산에 직접 반영되지 않음~~ → ✅ Phase 46 해결
- **해결**: 콜드스타트 보완 — 상호작용 <5건 시 preferred_genres → genre_counts fallback

### [A-3] ~~피드백 루프 체감 지연~~ → ✅ Phase 46 해결
- **해결**: interaction_version 캐시 무효화 키 도입 — 평점/찜 변경 시 추천 즉시 갱신

### [A-4] `weighted_score >= 6.0` 고정 하한으로 롱테일 노출 제한
- 현재 상태: 추천 주요 경로에서 6.0 하한이 고정으로 적용됨.  
  근거: `backend/app/api/v1/recommendation_engine.py:123`, `backend/app/api/v1/recommendations.py:65`
- 문제/리스크: 비주류·신규·취향 특화 콘텐츠 노출이 줄어 탐색 다양성 저하.
- 개선 방안: 사용자군별 동적 하한(예: 5.2~6.5), 세렌디피티 슬롯 확대, A/B 검증.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-1] ~~async 엔드포인트 내부 블로킹 I/O/CPU 처리~~ → ✅ Phase 48 해결
- **해결**: bcrypt → asyncio.to_thread(), httpx AsyncClient 싱글톤 (lifespan 관리), OAuth 통합

### [B-2] ~~런타임 `create_all` + 수동 SQL 마이그레이션 구조~~ → ✅ Phase 48 해결
- **해결**: Alembic 도입, Base.metadata.create_all() 제거, 빈 baseline stamp

### [B-3] ~~Rate limit 신뢰 경계 취약~~ → ✅ Phase 41 해결
- **해결**: 프록시 인식 IP 추출 강화

### [B-4] 인증 토큰 localStorage 저장
- 현재 상태: access/refresh 토큰을 localStorage에 저장.  
  근거: `frontend/stores/authStore.ts:31`, `frontend/stores/authStore.ts:55`
- 문제/리스크: XSS 발생 시 토큰 탈취 위험.
- 개선 방안: HttpOnly/Secure/SameSite 쿠키 기반 전환 + CSRF 방어.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-5] ~~빌드 시 외부 대용량 파일 직접 다운로드~~ → ✅ Phase 48 해결
- **해결**: Dockerfile에 SHA256 체크섬 무결성 검증 추가 (4개 파일)

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

### [A-8] ~~시맨틱 검색 재랭킹의 인기 편향~~ → ✅ Phase 49 해결
- **해결**: 재랭킹 v2 — semantic 60% + popularity 15% (log1p) + quality 25% (인기 편향 감소)

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

### [B-7] ~~관측성(로그 구조화/SLO/알람) 고도화 필요~~ → ✅ Phase 49 해결
- **해결**: structlog 구조화 로깅 (JSON prod/colored dev) + X-Request-ID 미들웨어

### [B-8] ~~테스트 게이트 부족~~ → ✅ Phase 49 해결
- **해결**: pytest 기본 스위트 (14건) + CI backend-test job (배포 필수 게이트)

### [B-9] 데이터 갱신 파이프라인 자동화 부족
- 현재 상태: 점수/태그/유사도 계산이 스크립트 수동 실행 중심.  
  근거: `backend/scripts/llm_emotion_tags.py`, `backend/scripts/compute_similar_movies.py`
- 문제/리스크: 신작 반영 지연, 운영자 의존 증가.
- 개선 방안: 주기 실행(cron/worker) + 실패 재시도 + 실행 상태 대시보드.
- 예상 난이도: Medium
- 예상 소요: 1.0 Phase

### [B-10] ~~GDPR/탈퇴 삭제 플로우 미비~~ → ✅ Phase 46 해결
- **해결**: DELETE /users/me 엔드포인트 + 연관 데이터 삭제 (ratings, collections, events)

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

## 로드맵 실행 결과 (Phase 46~50)

### 해결된 항목 (10/19)
- ✅ [A-2] 콜드스타트 — Phase 46
- ✅ [A-3] 피드백 루프 — Phase 46
- ✅ [A-8] 재랭킹 v2 — Phase 49
- ✅ [B-1] async 블로킹 — Phase 48
- ✅ [B-2] Alembic — Phase 48
- ✅ [B-3] Rate limit — Phase 41
- ✅ [B-5] 체크섬 — Phase 48
- ✅ [B-7] structlog — Phase 49
- ✅ [B-8] pytest — Phase 49
- ✅ [B-10] GDPR — Phase 46

### 미해결 항목 (향후 과제)
- [A-1] LLM 소스 판별 정확화
- [A-4] 롱테일 노출 조정
- [A-5] CF v2 (RecFlix 자체 데이터 기반)
- [A-6] 시간 감쇠 반영
- [A-9] 한국어 검색 전처리
- [B-4] 토큰 저장 방식 (HttpOnly Cookie)
- [B-6] 응답 페이로드 경량화
- [B-9] 데이터 갱신 배치 자동화
- [A-10] 컨텍스트 밴딧
- [A-11] 품질 대시보드
- [B-11] staging 환경
- [B-12] 인덱스 운영 자동화

---

## 총평
Phase 46~50에서 19개 지적사항 중 10개를 해결하여 **v1.0.0 릴리스** 달성. 핵심 운영 이슈(async 블로킹, Alembic, structlog, pytest, GDPR)와 추천 품질(콜드스타트, 피드백 루프, 재랭킹 v2)이 모두 해결됨. 남은 항목은 주로 고도화(CF v2, 밴딧, staging 환경) 및 UX 개선(토큰 보안, 페이로드 경량화) 영역.
