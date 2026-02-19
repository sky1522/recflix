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
