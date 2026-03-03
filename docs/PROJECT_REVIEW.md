# RecFlix 프로젝트 리뷰 & 로드맵

**최종 업데이트**: 2026-03-03

---

## 1. 초기 기획 vs 현재 구현 달성도

| 영역 | 초기 기획 (Phase 1-8) | 현재 구현 (Phase 54) | 변화 |
|------|----------------------|---------------------|------|
| **영화 데이터** | 32,625편 (CSV 1차) | **42,917편** (+31.5%) | 신규 CSV 마이그레이션 |
| **DB 컬럼** | 18개 기본 컬럼 | **23개** (+7, -2 정리) | director, cast_ko, weighted_score, trailer_key 등 추가 |
| **추천 요소** | MBTI + 날씨 + 개인취향 (3요소) | **MBTI + 날씨 + 기분 + 개인취향 + CF (5요소)** | Mood + SVD 협업 필터링 추가 |
| **추천 가중치** | MBTI 35% / Weather 25% / Personal 40% | **MBTI 20% / Weather 15% / Mood 25% / Personal 15% / CF 25%** | v3 튜닝 + CF 통합 |
| **추천 파이프라인** | 없음 (Content-based만) | **Two-Tower + LGBM Reranker + A/B 테스트** | ML 파이프라인 v2.0 |
| **감정 분석** | 없음 (Rule-based 점수만) | **2-Tier 시스템** (LLM 1,711편 + 키워드 41,206편) | Claude API 연동 |
| **품질 필터** | 없음 | **weighted_score >= 6.0** + 연속 보정(x0.85~1.0) | 정밀 품질 관리 |
| **연령등급** | certification 컬럼만 존재 | **4단계 필터링** (all/family/teen/adult) 전 API 적용 | 실질적 필터 구현 |
| **API 엔드포인트** | ~12개 | **24개+** (LLM, emotion, hybrid, events, ab-report 등) | 기능 확장 |
| **프론트엔드 페이지** | 6개 기본 페이지 | **12개 페이지** + 모달 + 모바일 네비게이션 | UX 고도화 |
| **테마** | 다크 모드 고정 | **다크/라이트 모드** (CSS 변수 시맨틱 토큰) | 테마 시스템 |
| **인증** | 이메일/비밀번호만 | **이메일 + Kakao + Google OAuth** | 소셜 로그인 |
| **배포** | Docker 설정만 | **Vercel + Railway + CI/CD** 프로덕션 운영 중 | 자동 배포 |

---

## 2. 기획에 없었지만 추가된 핵심 기능

| 기능 | Phase | 설명 |
|------|-------|------|
| **LLM 캐치프레이즈** | 10 | Claude API로 영화별 맞춤 문구 생성 + Redis 캐싱 |
| **emotion_tags 2-Tier** | 11, 14 | LLM 정밀 분석(1,711편) + 키워드 기반(41,206편) |
| **기분(Mood) 추천** | 11 | 6가지 기분 → 7대 감성 클러스터 매핑 |
| **30% LLM 보장 혼합 정렬** | 11 | 추천 풀에서 LLM 분석 영화 최소 30% 보장 |
| **새로고침 버튼** | 11 | Fisher-Yates 셔플, API 호출 없이 UI 재배치 |
| **연령등급 필터** | 14 | NULL 등급 처리 포함 4단계 필터링 |
| **날씨 한글 도시명** | 16 | Reverse Geocoding API + 70개+ 매핑 |
| **모듈 레벨 캐싱** | 17 | 페이지 네비게이션 시 추천 데이터 보존 |
| **시맨틱 검색** | 33 | Voyage AI 벡터 임베딩 + 자연어 질의 |
| **추천 다양성 정책** | 34 | 장르 다양성, 신선도, Serendipity 삽입 |
| **SVD 협업 필터링** | 35 | MovieLens 25M 매핑, 5축 하이브리드 |
| **CI/CD + 헬스체크** | 36 | GitHub Actions + Railway CD + /health |
| **추천 이유 생성** | 37 | 43개 한국어 템플릿, 비용 $0 |
| **트레일러 연동** | 47 | TMDB 28,486편 YouTube 트레일러 |
| **pytest 테스트** | 49 | 14건 (auth, health, movies, recommendations) |
| **structlog 로깅** | 49 | JSON 구조화 로깅 + X-Request-ID |
| **모바일 UI/UX** | 51 | 터치 44px, thumb zone, hover 대응 |
| **A/B 테스트 고도화** | 52 | Z-test 유의성, 이벤트 사각지대 해소 |
| **Two-Tower + Reranker** | 53 | PyTorch FAISS + LightGBM CTR 예측 |
| **다크/라이트 모드** | 54 | CSS 변수 시맨틱 토큰, 40개+ 컴포넌트 |
| **설정 페이지** | 54 | /settings — 닉네임, MBTI, 장르, 테마 |

---

## 3. 추천 알고리즘 진화 과정

```
Phase 6 (초기)
  Score = 0.35*MBTI + 0.25*Weather + 0.40*Personal
  필터: 없음

Phase 11 (emotion 도입)
  Score = 0.30*MBTI + 0.20*Weather + 0.20*Mood + 0.30*Personal
  필터: vote_count >= 30, vote_average >= 5.0

Phase 14 (v2 최종)
  Score = 0.25*MBTI + 0.20*Weather + 0.30*Mood + 0.25*Personal
  필터: weighted_score >= 6.0
  보정: x0.85~1.0 연속 품질 보정

Phase 35 (v3, CF 통합)
  Score = 0.20*MBTI + 0.15*Weather + 0.25*Mood + 0.15*Personal + 0.25*CF
  CF: SVD item_bias 기반 품질 점수 (MovieLens 25M 학습)

Phase 53 (v2.0, ML 파이프라인)
  Two-Tower Retriever: PyTorch + FAISS (42,917 items → 200 후보)
  LGBM Reranker: LightGBM CTR 예측 (200→50→20)
  A/B: control=hybrid_v1, test_a=twotower_lgbm_v1, test_b=twotower_v1
```

### 주요 변경 포인트

- **Mood 가중치 강화** (0.20 → 0.30): 사용자가 선택한 기분이 추천에 가장 큰 영향을 미치도록 조정
- **MBTI/Personal 완화** (0.30 → 0.25): 특정 요소의 과잉 지배 방지
- **품질 필터 통합**: 2중 조건(vote_count + vote_average) → 단일 weighted_score 기준으로 단순화
- **연속 품질 보정**: binary bonus(+0.1/+0.2) → weighted_score 기반 x0.85~1.0 곱셈으로 부드러운 품질 반영

---

## 4. 데이터 진화

| 항목 | Phase 1 (초기) | Phase 54 (현재) |
|------|---------------|----------------|
| 영화 수 | 32,625편 | 42,917편 |
| 평균 평점 | 5.92 | 6.31 |
| DB 컬럼 | 18개 | 23개 |
| emotion_tags | 없음 | 42,917편 (100%) |
| mbti_scores | 32,625편 | 42,917편 (100%) |
| weather_scores | 32,625편 | 42,917편 (100%) |
| trailer_key | 없음 | 28,486편 (66.4%) |
| similar_movies | 없음 | 429,170개 관계 (Top 10) |
| 관계 데이터 | 장르/출연진만 | + 키워드, 제작국, 유사영화 |
| ML 모델 | 없음 | SVD + Two-Tower + LGBM |
| reco_* 테이블 | 없음 | impressions, interactions, judgments |

### emotion_tags 2-Tier 시스템

| 방식 | 대상 | 영화 수 | 최대 점수 | 정밀도 |
|------|------|--------|----------|--------|
| **LLM 분석** (Claude API) | 인기 상위 | ~1,711 | 1.0 | 높음 (연속 분포) |
| **키워드 기반** | 나머지 | ~41,206 | 0.7 (상한) | 중간 (규칙 기반) |

---

## 5. 고도화 제안 (로드맵)

### A. 단기 — ✅ 모두 완료

| # | 제안 | 상태 | 완료 Phase |
|---|------|------|-----------|
| 1 | **검색 결과 하이라이팅** | ✅ 완료 | Phase 21 (HighlightText 컴포넌트) |
| 2 | **유사 영화 섹션 강화** | ✅ 완료 | Phase 23 (자체 유사도 엔진, 429,170관계) |
| 3 | **SEO 메타태그 최적화** | ✅ 완료 | Phase 24 (generateMetadata, OG 태그) |
| 4 | **에러 바운더리 추가** | ✅ 완료 | Phase 25 (error.tsx, not-found.tsx) |

### B. 중기 — ✅ 대부분 완료

| # | 제안 | 상태 | 완료 Phase |
|---|------|------|-----------|
| 5 | **소셜 로그인** | ✅ 완료 | Phase 31 (Kakao + Google OAuth) |
| 6 | **시청 기록 기반 추천 강화** | ✅ 완료 | Phase 46A (클릭/평점 피드백 루프) |
| 7 | **추천 이유 설명 강화** | ✅ 완료 | Phase 37 (43개 한국어 템플릿) |
| 8 | **PWA 지원** | ⬜ 미완료 | — |
| 9 | **다크모드/라이트모드** | ✅ 완료 | Phase 54 (CSS 변수 시맨틱 토큰) |

### C. 장기 — ✅ 대부분 완료

| # | 제안 | 상태 | 완료 Phase |
|---|------|------|-----------|
| 10 | **CI/CD 파이프라인** | ✅ 완료 | Phase 36 (GitHub Actions + Railway CD) |
| 11 | **A/B 테스트 프레임워크** | ✅ 완료 | Phase 32, 52 (그룹 배정, Z-test 유의성) |
| 12 | **Collaborative Filtering** | ✅ 완료 | Phase 35 (SVD, MovieLens 25M) |
| 13 | **실시간 트렌딩** | ⬜ 미완료 | — |
| 14 | **모니터링** | ✅ 완료 | Phase 29 (Sentry) + Phase 49 (structlog) |

### D. 데이터 품질 개선

| # | 제안 | 설명 |
|---|------|------|
| 15 | **10,292편 신규 영화 LLM 재분석** | 현재 키워드 기반(상한 0.7) → LLM 정밀 분석으로 추천 정밀도 향상 |
| 16 | **MBTI/Weather 점수 고도화** | 현재 장르+감정 규칙 기반 → LLM 분석 결과를 활용한 2차 보정 |
| 17 | **overview NULL 영화 처리** | 줄거리 없는 영화의 emotion_tags 정밀도 개선 |

---

## 6. 기술 부채 (Technical Debt)

| 항목 | 현재 상태 | 비고 |
|------|----------|------|
| **테스트 코드** | ✅ pytest 14건 (Phase 49) | 프론트엔드 테스트 미구현 |
| **타입 안전성** | ✅ `any` 0건 (Phase 45) | strict 모드 |
| **API 문서** | Swagger 자동 생성 | 사용 예시 보강 여지 |
| **환경 분리** | 로컬/프로덕션 2개 | 스테이징 환경 미구현 |
| **DB 마이그레이션** | ✅ Alembic (Phase 48) | reco_* 테이블 마이그레이션 완료 |
| **보안** | ✅ Rate Limiting (Phase 29) | CSRF 토큰 미구현 |
| **로깅** | ✅ structlog (Phase 49) | JSON 구조화 + X-Request-ID |
| **에러 추적** | ✅ Sentry (Phase 29) | Backend + Frontend |

---

## 7. 종합 평가

### 달성한 것

- 초기 Phase 1-8 기획 대비 **54 Phase까지 확장**, 단순 MBTI+날씨 추천에서 **5요소 Hybrid + ML 파이프라인 (Two-Tower + LGBM)**까지 발전
- 42,917편 영화 DB와 Vercel + Railway **프로덕션 운영 중** + CI/CD 자동 배포
- Netflix/Watcha 수준의 반응형 UI + 모바일 최적화 + 다크/라이트 모드
- 실시간 날씨 연동 + 기분 + MBTI 기반 추천이라는 **차별화된 UX**
- 소셜 로그인(Kakao/Google), A/B 테스트, 이벤트 추적 등 **서비스 운영 기반** 구축
- 로드맵 14개 항목 중 **12개 완료** (85.7% 달성)

### 남은 로드맵 항목

1. **PWA 지원** - manifest.json + Service Worker (앱 설치, 오프라인 지원)
2. **실시간 트렌딩** - 최근 24시간 조회/찜 기반 "지금 뜨는 영화" 섹션

---

## 관련 문서

- [PROGRESS.md](../PROGRESS.md) - Phase별 개발 진행 상황
- [CHANGELOG.md](../CHANGELOG.md) - 날짜별 변경 이력
- [RECOMMENDATION_LOGIC.md](RECOMMENDATION_LOGIC.md) - 추천 알고리즘 상세
- [DATA_PREPROCESSING.md](DATA_PREPROCESSING.md) - 데이터 전처리 과정
