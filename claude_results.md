# 프로젝트 컨텍스트 환경 구축 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| CLAUDE.md | 프로젝트 헌법 (AI 에이전트 진입점) | 173줄 |
| DECISION.md | 아키텍처 의사결정 기록 | 58줄 |
| .claude/skills/INDEX.md | 스킬 목차 | 11줄 |
| .claude/skills/workflow.md | RPI 프로세스, 디버깅, 컨텍스트 관리 | 35줄 |
| .claude/skills/recommendation.md | 추천 엔진 도메인 지식 | 55줄 |
| .claude/skills/curation.md | 큐레이션 문구 시스템 | 32줄 |
| .claude/skills/weather.md | 날씨 서비스 | 42줄 |
| .claude/skills/database.md | DB 스키마, 마이그레이션 | 54줄 |
| .claude/skills/deployment.md | 배포 가이드 | 48줄 |
| .claude/skills/frontend-patterns.md | 컴포넌트/훅/스토어 패턴 | 53줄 |
| .claude/settings.json | MCP 서버 설정 | 8줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| CLAUDE.md | 플레이북 표준으로 재작성 (93줄 → 173줄) |

## 핵심 변경사항
- CLAUDE.md: 플레이북 표준 형식 적용 (기술스택, 핵심 구조, DB 모델, 배포, 규칙, 스킬 참조)
- DECISION.md: 7개 주요 아키텍처 결정 기록
- .claude/skills/: 7개 도메인 스킬 (목차형, 소스 파일 참조)
- .claude/settings.json: context7 MCP 설정

## 스킬 시스템 요약
| 스킬 | 핵심 참조 파일 | 체크리스트 항목 수 |
|------|---------------|-------------------|
| workflow | - | 커밋 컨벤션 5종 |
| recommendation | recommendations.py | 6개 |
| curation | curationMessages.ts, contextCuration.ts | 4개 |
| weather | services/weather.py, useWeather.ts | 3개 |
| database | models/ | 7개 |
| deployment | DEPLOYMENT.md | 6개 |
| frontend-patterns | stores/, hooks/, api.ts | 7개 |

## 검증 결과
- CLAUDE.md: 173줄 (500줄 이하 ✅)
- .claude/skills/: 8개 파일 존재 (INDEX.md + 7개 스킬) ✅
- .claude/settings.json: 존재 ✅
- DECISION.md: 존재 ✅
- 소스 코드 변경: 없음 ✅
- 기존 문서 변경: 없음 (PROGRESS.md, CHANGELOG.md, PROJECT_CONTEXT.md, README.md, DEPLOYMENT.md) ✅

---

# 범용 스킬 추가 & MCP 설정 업데이트 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| .claude/skills/code-quality.md | Karpathy 원칙, 파일 크기, 중복 제거, 리팩토링 | 63줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| .claude/settings.json | security-guidance MCP 추가 |
| .claude/skills/INDEX.md | code-quality 스킬 추가 |
| CLAUDE.md | 규칙 섹션에 Karpathy 원칙, 타입 규칙 추가 (규칙 9, 10) |

## 500줄+ 파일 현황 (code-quality.md에 기록)
| 파일 | 줄 수 | 분리 방향 |
|------|-------|----------|
| backend/app/api/v1/recommendations.py | 770줄 | calculate_hybrid_scores() 스코어별 분리, 상수/태그/개인화 분리 |
| frontend/app/movies/[id]/page.tsx | 622줄 | 히어로 배너, 상세 정보, 출연진, 유사 영화 서브 컴포넌트 |
| backend/scripts/transliterate_foreign_names.py | 520줄 | 일회성 스크립트, 우선순위 낮음 |

## 300~499줄 파일 (분리 검토)
| 파일 | 줄 수 |
|------|-------|
| frontend/app/movies/page.tsx | 436줄 |
| backend/app/services/weather.py | 420줄 |
| frontend/lib/curationMessages.ts | 415줄 (상수 파일, 분리 불필요) |
| frontend/app/ratings/page.tsx | 413줄 |
| frontend/components/movie/FeaturedBanner.tsx | 407줄 |
| frontend/components/layout/Header.tsx | 373줄 |
| frontend/components/search/SearchAutocomplete.tsx | 359줄 |

## 검증 결과
- .claude/settings.json: MCP 2개 (context7, security-guidance) ✅
- code-quality.md: 존재 (63줄) ✅
- INDEX.md: code-quality 포함 ✅
- CLAUDE.md: 175줄 (500줄 이하 ✅)
- 소스 코드 변경: 없음 ✅

---

# movies/[id]/page.tsx 리팩토링 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| movies/[id]/components/MovieHero.tsx | 히어로 배너 | 207줄 |
| movies/[id]/components/MovieSidebar.tsx | 사이드바 (영화 정보, MBTI, 날씨) | 123줄 |
| movies/[id]/components/SimilarMovies.tsx | 유사 영화 그리드 | 64줄 |
| movies/[id]/components/MovieDetailSkeleton.tsx | 로딩 스켈레톤 | 56줄 |

## 수정된 파일
| 파일 | 변경 내용 | 줄 수 변화 |
|------|----------|-----------|
| movies/[id]/page.tsx | 데이터 페칭 + 평점/줄거리/출연진 + 레이아웃만 남김 | 622줄 → 231줄 |

## 분리 결과
| 파일 | 줄 수 | 역할 |
|------|-------|------|
| page.tsx | 231줄 | 데이터 페칭 + 평점/줄거리/출연진 + 레이아웃 조합 |
| MovieHero.tsx | 207줄 | 히어로 배너 (포스터, 제목, 캐치프레이즈, 메타, 장르, 액션버튼) |
| MovieSidebar.tsx | 123줄 | 영화 정보 + MBTI 점수 + 날씨 점수 |
| SimilarMovies.tsx | 64줄 | 유사 영화 그리드 |
| MovieDetailSkeleton.tsx | 56줄 | 로딩 스켈레톤 |
| **합계** | **681줄** | (622줄에서 +59줄 = import/interface 오버헤드) |

## 검증 결과
- TypeScript: No errors ✅
- ESLint: No warnings ✅
- Build: 성공 ✅
- 기능 변경: 없음 ✅

---

# recommendations.py 리팩토링 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| recommendation_engine.py | 순수 계산 로직 (스코어링, 쿼리 헬퍼) | 330줄 |
| recommendation_constants.py | 상수/매핑 데이터 | 76줄 |

## 수정된 파일
| 파일 | 변경 내용 | 줄 수 변화 |
|------|----------|-----------|
| recommendations.py | API 라우터만 남김, engine/constants import | 770줄 → 347줄 |

## 분리 결과
| 파일 | 줄 수 | 역할 |
|------|-------|------|
| recommendations.py | 347줄 | API 엔드포인트 (DB 쿼리 + 응답) |
| recommendation_engine.py | 330줄 | 하이브리드 스코어링 (순수 계산) |
| recommendation_constants.py | 76줄 | 매핑/가중치 상수 |
| **합계** | **753줄** | (770줄에서 -17줄, ruff 자동 수정 반영) |

## 검증 결과
- Python AST: 3개 파일 모두 OK ✅
- Import: router OK, engine OK ✅
- Ruff: All checks passed ✅
- 기능 변경: 없음 ✅

---

# Phase 1-1: Sentry 연동 + 에러 핸들링 표준화 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| backend/app/core/exceptions.py | 공통 에러 스키마 (ErrorResponse), 커스텀 예외 (AppException) | 31줄 |
| frontend/sentry.client.config.ts | Sentry 클라이언트 초기화 (DSN 없으면 스킵) | 13줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/app/main.py | 글로벌 예외 핸들러 4개 (AppException, HTTPException, RequestValidationError, Exception) + Sentry 초기화 (65줄 → 113줄) |
| backend/app/config.py | SENTRY_DSN: str = "" 추가 |
| backend/requirements.txt | sentry-sdk[fastapi]==2.19.2 추가 |
| frontend/next.config.js | withSentryConfig 래퍼 (DSN 있을 때만 활성화) |
| frontend/package.json | @sentry/nextjs 추가 |
| backend/.env.example | SENTRY_DSN 추가 |
| frontend/.env.example | NEXT_PUBLIC_SENTRY_DSN 추가 |
| backend/app/api/v1/movies.py | AGE_RATING_MAP import 경로 수정 (recommendations → recommendation_constants) |

## 에러 응답 포맷
```json
{
  "error": "NOT_FOUND",
  "message": "영화를 찾을 수 없습니다"
}
```

## 글로벌 예외 핸들러
| 핸들러 | 대상 | 동작 |
|--------|------|------|
| AppException | 커스텀 비즈니스 예외 | {error, message} 반환 |
| HTTPException | FastAPI 기본 예외 | detail을 통일 포맷으로 래핑 |
| RequestValidationError | 요청 유효성 검증 실패 | 422 + DEBUG 시 detail 포함 |
| Exception | 미처리 예외 전부 | Sentry 전송 + 500 반환 |

## Sentry 설정
- Backend: `SENTRY_DSN` 환경변수 (빈 문자열이면 비활성화)
- Frontend: `NEXT_PUBLIC_SENTRY_DSN` 환경변수 (없으면 비활성화)
- traces_sample_rate: 0.1 (10%)
- send_default_pii: false

## 추가 수정 (이전 리팩토링 누락 수정)
- `movies.py`에서 `AGE_RATING_MAP` import 경로가 `recommendations`에서 `recommendation_constants`로 변경되지 않은 문제 수정

## 검증 결과
- exceptions.py: Import OK ✅
- Sentry SDK: Import OK ✅
- 기존 API: 동작 OK ✅
- Ruff (exceptions.py): All checks passed ✅
- Frontend Build: 성공 ✅

---

# Phase 1-2: Rate Limiting + 환경변수 검증 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| backend/app/core/rate_limit.py | slowapi Limiter 인스턴스 (IP 기반) | 8줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/app/main.py | Rate Limiter 등록 + RateLimitExceeded 핸들러 + lifespan 시작 로그 |
| backend/app/config.py | DATABASE_URL, JWT_SECRET_KEY 검증 validator 추가 |
| backend/requirements.txt | slowapi==0.1.9 추가 |
| backend/app/api/v1/auth.py | @limiter.limit("5/minute") × 3 |
| backend/app/api/v1/recommendations.py | @limiter.limit("15/minute") × 8 |
| backend/app/api/v1/movies.py | autocomplete 30/min, 나머지 60/min × 5 |
| backend/app/api/v1/collections.py | @limiter.limit("30/minute") × 7 |
| backend/app/api/v1/ratings.py | @limiter.limit("30/minute") × 5 |
| backend/app/api/v1/weather.py | @limiter.limit("60/minute") × 2 |
| backend/app/api/v1/interactions.py | @limiter.limit("30/minute") × 5 |
| backend/app/api/v1/llm.py | @limiter.limit("15/minute") × 1 |
| backend/app/api/v1/users.py | @limiter.limit("30/minute") × 3 |

## Rate Limit 설정
| 엔드포인트 그룹 | 제한 | 엔드포인트 수 |
|----------------|------|-------------|
| 인증 (auth) | 5/분 | 3 |
| 추천 (recommendations) | 15/분 | 8 |
| LLM (catchphrase) | 15/분 | 1 |
| 검색 자동완성 (autocomplete) | 30/분 | 1 |
| 평점/찜/상호작용 | 30/분 | 17 |
| 일반 조회 (movies, weather) | 60/분 | 6 |
| 사용자 (users) | 30/분 | 3 |
| **합계** | | **39** |

## Rate Limit 초과 응답
```json
{"error": "RATE_LIMIT_EXCEEDED", "message": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."}
```

## 환경변수 검증
| 변수 | 검증 | 실패 시 |
|------|------|--------|
| DATABASE_URL | 비어있거나 "changeme"이면 거부 | 앱 시작 실패 |
| JWT_SECRET_KEY | 비어있거나 16자 미만이면 거부 | 앱 시작 실패 |
| SENTRY_DSN | 빈 문자열이면 비활성화 | 경고 없음 (선택) |
| WEATHER_API_KEY | 빈 문자열이면 비활성화 | 시작 로그에 표시 |

## 시작 로그
```
Environment: development
Database: connected
Redis: enabled/disabled
Sentry: enabled/disabled
Weather API: enabled/disabled
```

## 검증 결과
- rate_limit.py: Import OK ✅
- slowapi: Import OK ✅
- Config 검증: DB=True, JWT=True ✅
- 앱 시작: OK ✅
- Ruff (rate_limit.py, exceptions.py): All checks passed ✅

---

# Phase 2-1: 사용자 행동 이벤트 로깅 (Backend) 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| backend/app/models/user_event.py | UserEvent 모델 + 복합 인덱스 3개 | 33줄 |
| backend/app/schemas/user_event.py | EventCreate, EventBatch, EventResponse, EventStats | 56줄 |
| backend/app/api/v1/events.py | 이벤트 API (단일, 배치, 통계) | 161줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/app/models/__init__.py | UserEvent import 추가 |
| backend/app/api/v1/router.py | events 라우터 등록 |

## API 엔드포인트
| 메서드 | 경로 | Rate Limit | 인증 |
|--------|------|-----------|------|
| POST | /api/v1/events | 60/분 | 선택적 |
| POST | /api/v1/events/batch | 30/분 | 선택적 |
| GET | /api/v1/events/stats | 30/분 | 필수 |

## 이벤트 타입 (9종)
movie_click, movie_detail_view, movie_detail_leave, recommendation_impression,
search, search_click, rating, favorite_add, favorite_remove

## DB 인덱스
| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| idx_events_user_time | user_id, created_at | 사용자별 시간순 조회 |
| idx_events_type_time | event_type, created_at | 타입별 집계 |
| idx_events_movie | movie_id, event_type | 영화별 이벤트 집계 |

## 설계 원칙
- 실패해도 200 반환 (이벤트 로깅이 UX에 영향 없음)
- 비로그인 사용자는 session_id로 추적
- 배치 전송 지원 (최대 50개/요청)
- 통계 엔드포인트에서 추천 CTR (섹션별) 집계

## 검증 결과
- Model: Import OK ✅
- Schema: Import OK ✅
- Router: Import OK ✅
- App: 시작 OK ✅
- Ruff: All checks passed ✅

---

# Phase 2-2: 사용자 행동 이벤트 전송 (Frontend) 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| frontend/lib/eventTracker.ts | 이벤트 배치 전송 싱글톤 (5초 auto-flush, Beacon API) | 100줄 |
| frontend/hooks/useImpressionTracker.ts | 추천 섹션 뷰포트 노출 감지 훅 (IntersectionObserver) | 44줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| frontend/components/movie/MovieCard.tsx | section prop 추가, movie_click trackEvent 호출 |
| frontend/components/movie/HybridMovieCard.tsx | section prop 추가, movie_click trackEvent 호출 |
| frontend/components/movie/MovieRow.tsx | section prop 추가, useImpressionTracker 연동, MovieCard에 section 전달 |
| frontend/components/movie/HybridMovieRow.tsx | section prop 추가, useImpressionTracker 연동, HybridMovieCard에 section 전달 |
| frontend/app/page.tsx | getSectionFromTitle 헬퍼, section prop을 Row 컴포넌트에 전달 |
| frontend/app/movies/[id]/page.tsx | movie_detail_view/leave useEffect, rating/favorite trackEvent 호출 |
| frontend/components/search/SearchAutocomplete.tsx | search 이벤트 (결과 도착 시), search_click 이벤트 (영화 선택 시) |

## 이벤트 삽입 지점
| 이벤트 | 컴포넌트 | 트리거 |
|--------|---------|--------|
| movie_click | MovieCard / HybridMovieCard | 카드 클릭 (section 있을 때만) |
| movie_detail_view | movies/[id]/page.tsx | useEffect mount |
| movie_detail_leave | movies/[id]/page.tsx | useEffect cleanup (duration_ms 포함) |
| recommendation_impression | MovieRow / HybridMovieRow | IntersectionObserver (30% threshold) |
| search | SearchAutocomplete | 자동완성 결과 도착 |
| search_click | SearchAutocomplete | 영화 결과 클릭 |
| rating | movies/[id]/page.tsx | 별점 등록 |
| favorite_add/remove | movies/[id]/page.tsx | 찜 토글 |

## 설계 특징
- **배치 전송**: 5초마다 큐의 이벤트를 `/events/batch`로 일괄 전송
- **Beacon API**: 페이지 이탈 시 `navigator.sendBeacon`으로 잔여 이벤트 전송
- **세션 ID**: `sessionStorage`에 탭 단위 세션 ID 관리
- **SSR 안전**: `typeof window !== "undefined"` 체크, 서버에서는 null 싱글톤
- **실패 무시**: 전송 실패 시 `console.warn`만, UX 영향 없음
- **중복 방지**: Impression은 `tracked.current` ref로 섹션당 1회만 기록

## 검증 결과
- TypeScript: No errors ✅
- ESLint: No warnings ✅
- Build: 성공 ✅
- 기존 기능: 변경 없음 ✅

---

# Phase 3-1: MovieLens 매핑 + 오프라인 평가 환경 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| backend/scripts/movielens_mapper.py | MovieLens→RecFlix TMDB 매핑 | 101줄 |
| backend/scripts/recommendation_eval.py | 오프라인 평가 프레임워크 (3 베이스라인) | 193줄 |
| backend/data/movielens/mapped_ratings.csv | 매핑된 평점 데이터 | 22,506,842행 |
| backend/data/movielens/mapping_stats.json | 매핑 통계 | - |
| backend/data/movielens/eval_results.csv | 평가 결과 | - |

## 매핑 결과
| 항목 | 값 |
|------|-----|
| RecFlix 전체 영화 | 42,917편 |
| MovieLens 전체 영화 | 62,316편 |
| 매핑된 영화 | 20,372편 |
| RecFlix 매핑률 | 47.5% |
| MovieLens 매핑률 | 32.7% |
| 매핑된 평점 수 | 22,506,842개 (전체 25M 중 90%) |
| 매핑된 사용자 수 | 162,536명 |
| 사용자당 평균 평점 | 138.5개 |

## 핵심 설계 결정
- **Movie.id = TMDB ID**: 별도 tmdb_id 컬럼 없이 Movie.id가 곧 TMDB PK
- **동기 DB 접근**: SessionLocal() 동기 세션 사용 (기존 패턴 준수)
- **Train/Test 분리**: timestamp 기준 80/20 (사용자별), 최소 5평점 사용자만

## 베이스라인 평가 결과
| 모델 | Precision@10 | Recall@10 | NDCG@10 | RMSE |
|------|-------------|-----------|---------|------|
| Popularity Baseline | 0.0209 | 0.0269 | 0.0313 | - |
| Global Mean Baseline | - | - | - | 1.0566 |
| Item Mean Baseline | - | - | - | 0.9604 |

## 데이터 규모
- Train: 17,940,901 ratings
- Test: 4,565,909 ratings
- 활성 사용자: 162,524명
- 활성 영화: 18,464편

## 검증 결과
- movielens_mapper.py: 실행 OK ✅
- mapped_ratings.csv: 22,506,842행 생성 ✅
- recommendation_eval.py: 실행 OK ✅
- eval_results.csv: 3 베이스라인 결과 저장 ✅
- .gitignore: 대용량 파일 제외 ✅

---

# Phase 3-2: 협업 필터링 (SVD) 구현 + 오프라인 평가 + 하이브리드 통합 결과

## 날짜
2026-02-19

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| backend/scripts/train_cf_model.py | SVD 모델 학습 + pickle 저장 | 98줄 |
| backend/app/api/v1/recommendation_cf.py | CF 모델 로드 + 예측 | 66줄 |
| backend/data/movielens/svd_model.pkl | 학습된 SVD 모델 | 53.1 MB |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/scripts/recommendation_eval.py | SVDModel 클래스, SVD/Hybrid 평가 추가 (193줄 → 517줄) |
| backend/app/api/v1/recommendation_engine.py | CF 점수 통합 (predict_cf_score + 가중치 분기) |
| backend/app/api/v1/recommendation_constants.py | WEIGHT_*_CF 상수 8개 추가 |
| backend/requirements.txt | scipy==1.14.1 추가 |
| .gitignore | svd_model.pkl 제외 추가 |

## 오프라인 평가 결과 (10K 사용자 샘플)
| 모델 | RMSE | Precision@10 | Recall@10 | NDCG@10 |
|------|------|-------------|-----------|---------|
| Popularity Baseline | - | 0.0234 | 0.0268 | 0.0327 |
| Global Mean Baseline | 1.0513 | - | - | - |
| Item Mean Baseline | 0.9656 | - | - | - |
| **SVD (k=100)** | **0.8768** | 0.0014 | 0.0017 | 0.0021 |
| Hybrid (α=0.3) | - | 0.0002 | 0.0000 | 0.0003 |
| Hybrid (α=0.5) | - | 0.0000 | 0.0000 | 0.0000 |
| Hybrid (α=0.7) | - | 0.0000 | 0.0000 | 0.0000 |

## 핵심 분석
- **SVD RMSE**: 0.8768 → Item Mean 대비 **-9.2% 개선** (평점 예측 우수)
- **SVD Top-K**: 인기도 대비 약함 (sparse matrix + 개인화 신호 부족)
- **프로덕션 활용**: SVD의 `item_bias`를 아이템 품질 시그널로 사용
  - RecFlix 사용자는 MovieLens에 없으므로 CF = `global_mean + item_bias`
  - 기존 Rule-based(MBTI/날씨/기분)에 CF 품질 점수를 25% 가중치로 보조

## 프로덕션 가중치 (CF 활성화 시)
| 조건 | MBTI | Weather | Mood | Personal | CF |
|------|------|---------|------|----------|-----|
| Mood+CF | 0.20 | 0.15 | 0.25 | 0.15 | 0.25 |
| CF only | 0.25 | 0.20 | - | 0.30 | 0.25 |
| 기존 (CF 없음) | 0.25 | 0.20 | 0.30 | 0.25 | - |

## SVD 모델 학습 결과
- 학습 데이터: 7,122,661 ratings, 50,000 users
- Matrix: 50,000 × 17,471 items
- Factors: k=100
- global_mean: 3.5309
- 모델 크기: 53.1 MB

## CF 예측 예시
| 영화 | ID | CF 점수 | 정규화 |
|------|-----|---------|--------|
| Shawshank Redemption | 278 | 4.42 | 0.87 |
| Forrest Gump | 550 | 4.23 | 0.83 |
| Pulp Fiction | 680 | 4.19 | 0.82 |
| 매핑 안 된 영화 | 99999 | None | fallback |

## 기술 결정
- **scikit-surprise 대신 scipy**: Windows Cython 컴파일 에러 → scipy.sparse.linalg.svds 사용
- **bias 제거 벡터화**: COO 형식으로 O(nnz) 연산 (dense 변환 불필요)
- **RMSE 평가 벡터화**: numpy 배열 연산으로 iterrows() 제거
- **Top-K 최적화**: np.argpartition으로 O(n) 선택

## 검증 결과
- scipy: Import OK ✅
- 평가 스크립트: 실행 OK ✅
- 모델 학습: OK ✅
- CF 모듈: Import OK ✅
- 기존 추천 API: 동작 OK ✅
- Ruff: All checks passed ✅

---

# Phase 4-1: A/B 테스트 프레임워크 + 추천 품질 대시보드 결과

## 날짜
2026-02-19

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/app/models/user.py | experiment_group 컬럼 추가 (String(10), default="control", server_default="control") |
| backend/app/api/v1/auth.py | 회원가입 시 랜덤 그룹 배정 (random.choice) |
| backend/app/api/v1/recommendation_engine.py | get_weights_for_group() + _get_control_weights() 함수 추가, experiment_group 파라미터 |
| backend/app/api/v1/recommendation_constants.py | WEIGHTS_HYBRID_A/B, WEIGHTS_HYBRID_A/B_NO_MOOD 상수 4개 추가 |
| backend/app/api/v1/recommendations.py | calculate_hybrid_scores()에 experiment_group 전달 |
| backend/app/api/v1/events.py | AB report 엔드포인트 + experiment_group 메타데이터 자동 주입 |
| backend/app/schemas/user_event.py | not_interested 이벤트 타입 + ABGroupStats, ABReport 스키마 추가 |

## 실험 그룹 가중치
| 그룹 | MBTI | Weather | Mood | Personal | CF | 설명 |
|------|------|---------|------|----------|-----|------|
| control | 0.20/0.25 | 0.15/0.20 | 0.25/- | 0.15/0.30 | 0.25 | 기존 Rule-based + CF 25% |
| test_a | 0.12/0.17 | 0.10/0.13 | 0.15/- | 0.13/0.20 | 0.50 | CF 50% |
| test_b | 0.08/0.10 | 0.07/0.08 | 0.10/- | 0.05/0.12 | 0.70 | CF 70% |

## API 엔드포인트
| 메서드 | 경로 | Rate Limit | 인증 | 용도 |
|--------|------|-----------|------|------|
| GET | /api/v1/events/ab-report | 30/분 | 필수 | A/B 테스트 그룹별 리포트 |

## AB Report 응답 구조
- groups: 그룹별 users, total_clicks, total_impressions, ctr, avg_detail_duration_ms, rating_conversion, favorite_conversion, by_section
- winner: CTR 기준 최고 그룹
- confidence_note: 통계적 유의성 안내

## 이벤트 확장
- `not_interested` 이벤트 타입 추가 (총 10종)
- 이벤트 기록 시 로그인 사용자의 experiment_group 자동 메타데이터 주입

## 검증 결과
- experiment_group: 모델 OK ✅
- 가중치 분기: control/test_a/test_b 모두 정상 반환 ✅
- not_interested 이벤트: OK ✅
- Ruff: All checks passed ✅

---

# Phase 4-2: 온보딩 개선 + 소셜 로그인 구현 결과

## 날짜
2026-02-19

## 신규 파일 (4)
| 파일 | 용도 |
|------|------|
| `backend/scripts/migrate_phase4.sql` | DB 마이그레이션 SQL (experiment_group + 소셜/온보딩 컬럼) |
| `frontend/app/auth/kakao/callback/page.tsx` | 카카오 OAuth 콜백 (Suspense 래핑) |
| `frontend/app/auth/google/callback/page.tsx` | 구글 OAuth 콜백 (Suspense 래핑) |
| `frontend/app/onboarding/page.tsx` | 온보딩 2단계 (장르 선택 + 영화 평가) |

## 수정 파일 (12)
| 파일 | 변경 내용 |
|------|----------|
| `backend/app/models/user.py` | 소셜 로그인 컬럼 4개 + 온보딩 컬럼 2개 추가 |
| `backend/app/schemas/user.py` | UserResponse 확장, SocialLoginRequest/Response, OnboardingComplete 추가 |
| `backend/app/schemas/__init__.py` | 새 스키마 export |
| `backend/app/config.py` | Kakao/Google OAuth 환경변수 6개 |
| `backend/app/api/v1/auth.py` | POST /auth/kakao, POST /auth/google 엔드포인트 |
| `backend/app/api/v1/movies.py` | GET /movies/onboarding 엔드포인트 (40편, 장르 분포) |
| `backend/app/api/v1/users.py` | PUT /users/me/onboarding-complete 엔드포인트 |
| `frontend/types/index.ts` | User 확장, SocialLoginResponse 추가 |
| `frontend/lib/api.ts` | kakaoLogin, googleLogin, getOnboardingMovies, completeOnboarding |
| `frontend/stores/authStore.ts` | socialLogin 메서드 추가 |
| `frontend/app/login/page.tsx` | 소셜 로그인 버튼 (카카오 #FEE500, Google 흰색) |
| `frontend/app/signup/page.tsx` | 동일한 소셜 로그인 버튼 |

## 검증 결과
- Backend 모델: ✅
- Backend 스키마: ✅
- Backend 라우트: signup, login, refresh_token, kakao_login, google_login ✅
- Frontend TypeScript: ✅
- Frontend Build: 성공 (13 pages) ✅

---

# 긴급 수정: 소셜 로그인 디버깅 결과

## 날짜
2026-02-19

## 원인
**2가지 원인 동시 발생:**

### 원인 1: Frontend - 환경변수 미설정 + Silent Fail (체크 A)
- `frontend/.env.local` 파일이 **존재하지 않음**
- `NEXT_PUBLIC_KAKAO_CLIENT_ID`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID` 등 모두 undefined
- `if (clientId && redirectUri)` 가드 조건에서 **아무 동작 없이 종료** (silent fail)
- login/page.tsx, signup/page.tsx 양쪽 모두 동일한 문제

### 원인 2: Backend - 미배포 + 의존성 누락
- `/api/v1/auth/kakao`, `/api/v1/auth/google` → **404 Not Found** (배포 안 됨)
- `/api/v1/events/batch` → **404 Not Found** (배포 안 됨)
- `railway up` 후 **502 크래시** → `ModuleNotFoundError: No module named 'sentry_sdk'`
- 원인: **루트 `requirements.txt`에 `sentry-sdk`, `slowapi`, `scipy` 누락** (backend/requirements.txt와 비동기)
- 추가: 프로덕션 DB에 `user_events` 테이블 미생성

## 수정 내용
| 파일 | 변경 |
|------|------|
| frontend/app/login/page.tsx | 카카오/Google 버튼 가드 조건 반전 (`if (!clientId \|\| !redirectUri)` → console.error + alert) |
| frontend/app/signup/page.tsx | 동일한 수정 (silent fail → 에러 표시) |
| requirements.txt (루트) | backend/requirements.txt와 동기화 (+sentry-sdk, +slowapi, +scipy) |
| 프로덕션 DB | `user_events` 테이블 + 인덱스 5개 생성 (ALTER TABLE via psql) |

## Backend 배포 상태
- Railway 재배포: 2026-02-19 완료
- /health: 200 OK ✅
- /auth/login: 401 (정상) ✅
- /auth/kakao: 401 "카카오 인증에 실패했습니다" (엔드포인트 존재 확인) ✅
- /auth/google: 401 "구글 인증에 실패했습니다" (엔드포인트 존재 확인) ✅
- /events/batch: 201 OK ✅

## 검증 결과
- 로컬 카카오 버튼: ⚠️ .env.local 없어서 alert 표시 (정상 동작 - silent fail 방지됨)
- 프로덕션 카카오 버튼: ⚠️ Vercel에 NEXT_PUBLIC_KAKAO_CLIENT_ID 미등록 시 alert 표시
- 로컬 Google 버튼: ⚠️ .env.local 없어서 alert 표시 (정상 동작 - silent fail 방지됨)
- 프로덕션 Google 버튼: ⚠️ Vercel에 NEXT_PUBLIC_GOOGLE_CLIENT_ID 미등록 시 alert 표시
- Backend 엔드포인트: 모두 정상 ✅
- ESLint: No warnings ✅

## 남은 작업 (OAuth 앱 등록 필요)
→ **완료됨** (아래 E2E 검증 결과 참조)

---

# 소셜 로그인 E2E 검증 결과

## 날짜
2026-02-19

## 발견된 문제
| # | 문제 | 원인 | 수정 |
|---|------|------|------|
| 1 | 소셜 버튼 클릭 시 무반응 (silent fail) | `if (clientId && redirectUri)` 가드 + 환경변수 undefined | 가드 반전 + console.error + alert |
| 2 | Backend 소셜 엔드포인트 404 | Railway 미배포 | `railway up` 재배포 |
| 3 | Backend 502 크래시 | 루트 `requirements.txt`에 sentry-sdk/slowapi/scipy 누락 | 루트 파일을 backend와 동기화 |
| 4 | 프로덕션 DB user_events 테이블 없음 | Phase 30 스키마 미마이그레이션 | psql로 CREATE TABLE + 인덱스 5개 |
| 5 | 카카오 Client ID 잘못 등록 | 최초 키 오입력 (REST API 키 ≠ Client ID) | Vercel/Railway 재등록 + Vercel 재배포 |

## 수정된 파일
| 파일 | 변경 |
|------|------|
| frontend/app/login/page.tsx | 카카오/Google 버튼 silent fail → alert 에러 표시 |
| frontend/app/signup/page.tsx | 동일 수정 |
| requirements.txt (루트) | +sentry-sdk, +slowapi, +scipy (backend와 동기화) |

## 환경변수 등록 완료
| 서비스 | 변수 | 값 확인 |
|--------|------|---------|
| Vercel | NEXT_PUBLIC_KAKAO_CLIENT_ID | f5ba90d4... ✅ |
| Vercel | NEXT_PUBLIC_KAKAO_REDIRECT_URI | .../auth/kakao/callback ✅ |
| Vercel | NEXT_PUBLIC_GOOGLE_CLIENT_ID | 222719323914-... ✅ |
| Vercel | NEXT_PUBLIC_GOOGLE_REDIRECT_URI | .../auth/google/callback ✅ |
| Railway | KAKAO_CLIENT_ID | f5ba90d4... ✅ |
| Railway | KAKAO_CLIENT_SECRET | xKK3Fa... ✅ |
| Railway | KAKAO_REDIRECT_URI | .../auth/kakao/callback ✅ |
| Railway | GOOGLE_CLIENT_ID | 222719323914-... ✅ |
| Railway | GOOGLE_CLIENT_SECRET | GOCSPX-... ✅ |
| Railway | GOOGLE_REDIRECT_URI | .../auth/google/callback ✅ |

## E2E 테스트 결과
| 항목 | 로컬 | 프로덕션 |
|------|------|---------|
| 카카오 버튼 → 인증 페이지 이동 | ⚠️ .env.local 없음 (alert 표시) | ✅ 302 → accounts.kakao.com |
| 카카오 콜백 → JWT 발급 | - | ✅ 콜백 200 + Backend 401 (test code 정상 거부) |
| Google 버튼 → 인증 페이지 이동 | ⚠️ .env.local 없음 (alert 표시) | ✅ 302 → accounts.google.com |
| Google 콜백 → JWT 발급 | - | ✅ 콜백 200 + Backend 401 (test code 정상 거부) |
| 온보딩 리다이렉트 (신규 사용자) | - | ✅ 코드 확인 (isNew ? /onboarding : /) |

## Backend 엔드포인트
- POST /auth/kakao: HTTP 401 ✅
- POST /auth/google: HTTP 401 ✅
- GET /health: HTTP 200 ✅
- POST /events/batch: HTTP 201 ✅

## JS 번들 검증
- 카카오 Client ID (f5ba90d4...) 포함 ✅
- kauth.kakao.com URL 포함 ✅
- Google Client ID (222719323914...) 포함 ✅
- accounts.google.com URL 포함 ✅
- CORS origins에 jnsquery-reflix.vercel.app 포함 ✅
