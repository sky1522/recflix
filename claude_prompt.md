# RecFlix 프로젝트 컨텍스트 환경 구축

프로젝트의 AI 에이전트 협업 환경을 세팅한다. 충분히 탐색하고 시작해.

먼저 읽을 것:
- CLAUDE.md (이미 있으면 내용 확인, 플레이북 기준으로 보강 필요)
- pyproject.toml (Ruff 설정 확인)
- PROGRESS.md, CHANGELOG.md, PROJECT_CONTEXT.md (프로젝트 현황 파악)
- backend/app/api/v1/recommendations.py (핵심 비즈니스 로직, 스킬 작성 참고)
- frontend/app/page.tsx (홈 데이터 흐름, 스킬 작성 참고)
- frontend/lib/curationMessages.ts, contextCuration.ts (큐레이션 시스템 구조 파악)
- backend/app/services/weather.py (날씨 서비스 구조 파악)
- backend/app/services/llm.py (LLM 서비스 구조 파악)

---

=== 1단계: CLAUDE.md 재작성 ===

기존 CLAUDE.md를 **플레이북 표준 형식**으로 재작성한다.
500줄 이하 유지. 상세 지식은 스킬로 분산.

포함할 섹션:
```
# RecFlix
실시간 컨텍스트(날씨/기분)와 MBTI를 결합한 초개인화 영화 큐레이션 플랫폼.
https://jnsquery-reflix.vercel.app

## 기술스택
(한 문단: Next.js 14 App Router + TailwindCSS + Framer Motion + Zustand / FastAPI + SQLAlchemy + Pydantic + Redis / PostgreSQL 16 / Vercel + Railway)

## 핵심 구조
(트리 형태, 주요 파일만, 파일별 한 줄 설명)
backend/app/api/v1/recommendations.py  # ★ 하이브리드 추천 엔진 (770 LOC)
backend/app/api/v1/movies.py           # 검색, 상세, 자동완성
backend/app/services/weather.py        # 날씨 + 역지오코딩 + 70개 한글 도시명
backend/app/services/llm.py            # Claude API 캐치프레이즈 + Redis 캐싱
backend/app/config.py                  # pydantic-settings (env 기반)
frontend/app/page.tsx                  # ★ 홈 (배너 + 추천 Row + 큐레이션)
frontend/app/movies/[id]/page.tsx      # 영화 상세 (622 LOC)
frontend/lib/curationMessages.ts       # 258개 큐레이션 문구
frontend/lib/contextCuration.ts        # 시간대/계절/기온 감지
frontend/lib/api.ts                    # 24개 API 함수
frontend/stores/interactionStore.ts    # 찜/평점 Optimistic UI
frontend/hooks/useWeather.ts           # Geolocation + localStorage 캐시
... (나머지 주요 파일)

## DB 모델
movies: 22컬럼, 42,917행 (id=TMDB PK, title_ko, cast_ko 100% 한글, mbti_scores/weather_scores/emotion_tags JSONB)
similar_movies: 429,170개 관계 (자체 유사도 Top 10)
users: email UNIQUE, mbti, bcrypt password
ratings: user_id+movie_id UNIQUE, score 0.5~5.0
collections + collection_movies: 찜 관리
genres(19종), persons(97,206), keywords, countries: M:M 연결

## 배포
Frontend: Vercel (https://jnsquery-reflix.vercel.app)
Backend: Railway (https://backend-production-cff2.up.railway.app)
DB: Railway PostgreSQL + Redis
GitHub: https://github.com/sky1522/recflix

## 규칙
1. 작업 완료 시: git add -A && git commit -m 'type(scope): 설명' && git push origin HEAD:main
2. 결과는 claude_results.md에 저장 (날짜, 변경 파일, 핵심 변경사항, 검증 결과)
3. Python: logging 사용 (print 금지), Ruff 린트/포맷, 함수 100줄 이내
4. TypeScript: ESLint core-web-vitals, 상수는 constants.ts, 모듈 레벨 mutable 변수 금지
5. 환경변수에 시크릿 하드코딩 금지
6. DB 스키마 변경 시 JSONB 인덱스 확인
7. 추천 알고리즘 변경 시 docs/RECOMMENDATION_LOGIC.md 동기화
8. 복잡한 작업은 .claude/skills/workflow.md의 RPI 프로세스를 따른다

## 스킬
상세 지식은 `.claude/skills/` 참조. 인덱스: `.claude/skills/INDEX.md`
```

---

=== 2단계: DECISION.md 생성 ===

프로젝트의 주요 아키텍처 의사결정 기록. 기존 PROGRESS.md와 PROJECT_CONTEXT.md에서 추출하여 작성.

```markdown
# RecFlix Architecture Decisions

## 1. 추천 엔진: Rule-based Hybrid Scoring
- 현황: MBTI/날씨/기분/개인화 4축 하이브리드
- 결정: ML 모델 대신 Rule-based 가중치 스코어링 채택
- 근거: 42,917편 규모에서 실시간 응답 필요, 학습 데이터 부족, 가중치 직관적 튜닝 가능
- 대안 검토: 협업 필터링 (사용자 수 부족으로 기각), 콘텐츠 기반 추천 (JSONB 스코어로 대체)
- 가중치: Mood시 0.25/0.20/0.30/0.25, Mood없이 0.35/0.25/0.40

## 2. emotion_tags: 2-Tier 시스템 (LLM + 키워드)
- 현황: 7대 감성 클러스터 (healing, tension, energy, romance, deep, fantasy, light)
- 결정: 상위 1,711편은 Claude API 분석, 나머지 41,206편은 키워드 기반 생성
- 근거: LLM 분석 비용 ($11.69) 대비 전체 적용 불가, 키워드 기반 0.7 상한으로 품질 차등
- LLM 분석 영화: emotion_tags 값 ≤1.0, 키워드 기반: ≤0.7

## 3. 유사 영화: 자체 계산
- 결정: TMDB 유사 영화 대신 자체 코사인 유사도 사용
- 공식: 0.5×emotion코사인 + 0.3×mbti코사인 + 0.2×장르Jaccard + LLM보너스(0.05)
- 근거: RecFlix 자체 점수 체계와 일관된 추천, TMDB 유사도는 장르만 고려

## 4. cast_ko 한글화: Claude API 음역
- 결정: 42,759편 출연진 이름 100% 한글화
- 방법: Claude API로 4,253개 외국어 이름 음역 ($1.78)
- 근거: 한국 사용자 UX, 검색 편의성

## 5. 프론트엔드 상태관리: Zustand
- 결정: Redux/Recoil 대신 Zustand 채택
- 근거: 보일러플레이트 최소, 러닝커브 낮음, 2개 스토어(auth, interaction)로 충분

## 6. 배포: Vercel + Railway
- 결정: Frontend=Vercel, Backend+DB+Redis=Railway
- 근거: Next.js SSR 최적화(Vercel), PostgreSQL+Redis 통합 관리(Railway)
- 비용: ~$10-20/월

## 7. 큐레이션 문구: 정적 258개 시스템
- 결정: LLM 실시간 생성 대신 사전 정의 258개 문구
- 근거: 응답 속도, 비용 절약, 품질 일관성
- 구조: 시간대(24) + 계절(24) + 기온(24) + 날씨(24) + 기분(48) + MBTI(96) + 고정(18)
```

위 내용에서 실제 코드/설정을 확인하여 정확한 정보로 보강해줘.

---

=== 3단계: .claude/skills/ 디렉토리 구성 ===

스킬 파일 생성. **목차형** 원칙 준수 (상세 코드는 소스 파일로 유도, 체크리스트만 직접 유지).

### 3-1. .claude/skills/INDEX.md

```markdown
# Skills Index

| 스킬 | 설명 |
|------|------|
| workflow | RPI 프로세스, 디버깅 전략, 컨텍스트 관리, 프롬프트 패턴 |
| recommendation | 하이브리드 추천 엔진, 스코어링, 태그 시스템, 알고리즘 튜닝 |
| curation | 큐레이션 문구 시스템, 컨텍스트 감지, 258개 문구 구조 |
| weather | 날씨 서비스, OpenWeatherMap 연동, 역지오코딩, 한글 도시명 |
| database | DB 스키마, JSONB 점수, 마이그레이션, 인덱스 |
| deployment | Vercel/Railway 배포, 환경변수, CORS, CI/CD |
| frontend-patterns | 컴포넌트 구조, Zustand 스토어, 훅 패턴, Optimistic UI |
```

### 3-2. .claude/skills/workflow.md

RPI 프로세스를 RecFlix에 맞게 작성:

```markdown
# 워크플로우

## RPI 프로세스 (Research → Plan → Implement)

### 복잡한 작업 (3개+ 파일 수정, 원인 불명 버그, 새 기능)
1. Research: 관련 파일 열어서 구조 파악, grep 영향 범위, 유사 구현 패턴 검색
2. Plan: 수정 파일 목록 + 변경 함수/라인, 예상 부작용, 기존 패턴 재사용
3. Implement: 계획대로만 수정, 빌드 확인

### 간단한 작업 (1~2개 파일)
→ Research/Plan 생략 가능

## 디버깅: 2회 실패 규칙
같은 문제 2회 이상 실패 → Research부터 재시작, grep 전체 출력, 실패 원인 분석

## 컨텍스트 관리
- 500줄+ 파일은 grep으로 관련 함수만 (특히 recommendations.py 770줄)
- 스킬 파일 먼저 확인
- 한 번에 수정 3파일 이하
- 수정 전 기존 패턴 확인

## 검증
- Backend: python -c "import ast; ast.parse(open('파일').read())" 또는 ruff check
- Frontend: npx tsc --noEmit && npx next lint
- 전체: 각 변경 후 빌드 확인

## 커밋 컨벤션
feat(scope): 새 기능
fix(scope): 버그 수정
refactor(scope): 코드 구조 변경
docs: 문서/스킬 변경
chore: 설정/빌드/의존성
```

### 3-3. .claude/skills/recommendation.md

```markdown
# 추천 시스템

## 핵심 파일
→ backend/app/api/v1/recommendations.py 참조 (770 LOC)

## 하이브리드 스코어링
→ recommendations.py의 calculate_hybrid_scores() 참조
- Mood 있을 때: (0.25×MBTI) + (0.20×Weather) + (0.30×Mood) + (0.25×Personal)
- Mood 없을 때: (0.35×MBTI) + (0.25×Weather) + (0.40×Personal)
- 품질 보정: weighted_score 기반 ×0.85~1.0

## 추천 태그
→ recommendations.py의 태그 부여 로직 참조
- #MBTI추천 (스코어 > 0.5), #비오는날 등 (날씨 > 0.5), #취향저격 (장르 2개↑), #명작 (ws ≥ 7.5)

## MBTI/날씨/기분 매핑
→ recommendations.py의 MOOD_EMOTION_MAP, 날씨/MBTI 매핑 상수 참조

## 개인화 로직
→ recommendations.py의 Personal Score 계산 참조
1. 찜 + 고평점(4.0↑) 영화 장르 집계
2. 상위 3개 장르
3. similar_movies 보너스

## 알고리즘 변경 시 체크리스트
1. recommendations.py 가중치/로직 수정
2. docs/RECOMMENDATION_LOGIC.md 동기화
3. 추천 태그 조건 확인
4. 품질 필터(weighted_score >= 6.0) 영향 확인
5. 프론트엔드 HybridMovieCard 태그 표시 확인
6. 빌드 확인
```

### 3-4. .claude/skills/curation.md

```markdown
# 큐레이션 시스템

## 핵심 파일
→ frontend/lib/curationMessages.ts (258개 문구)
→ frontend/lib/contextCuration.ts (컨텍스트 감지)
→ frontend/app/page.tsx의 getRowSubtitle(), getHybridSubtitle()

## 문구 구조 (258개)
→ curationMessages.ts 참조
- WEATHER: 4종 × 6 = 24
- MOOD: 8종 × 6 = 48
- MBTI: 16종 × 6 = 96
- FIXED: 3종 × 6 = 18
- TIME: 4종 × 6 = 24
- SEASON: 4종 × 6 = 24
- TEMP: 6종 × 4 = 24

## 컨텍스트 감지
→ contextCuration.ts 참조
- 시간대: morning/afternoon/evening/night (getHours)
- 계절: spring/summer/autumn/winter (getMonth)
- 기온: freezing/cold/cool/mild/warm/hot (weather.temperature)

## 적용 위치
- 맞춤 추천 → TIME_SUBTITLES
- 날씨 추천 → 짝수 idx=SEASON, 홀수 idx=TEMP

## 문구 추가 시 체크리스트
1. curationMessages.ts에 문구 추가 (기존 구조 유지)
2. 시간/계절/기온 종속 표현 사용 금지 (중립적 표현만)
3. 하이드레이션 안전: useEffect에서만 컨텍스트 설정
4. 빌드 확인
```

### 3-5. .claude/skills/weather.md

```markdown
# 날씨 서비스

## 핵심 파일
→ backend/app/services/weather.py (420 LOC)
→ backend/app/api/v1/weather.py (141 LOC)
→ frontend/hooks/useWeather.ts (237 LOC)
→ frontend/components/weather/WeatherBanner.tsx (198 LOC)

## OpenWeatherMap 연동
→ weather.py의 API 호출 로직 참조
- 좌표 기반: /weather?lat=37.5&lon=127
- 도시 기반: /weather?city=Seoul

## 역지오코딩 + 한글 도시명
→ weather.py의 reverse_geocode + 70개 한글 도시명 매핑 참조

## 캐싱
→ weather.py의 Redis 캐싱 참조
- 키: weather:v2:coords:{lat}:{lon}, weather:v2:city:{city}
- TTL: 30분
→ useWeather.ts의 localStorage 캐싱 참조
- 키: constants.ts의 WEATHER_CACHE_KEY (recflix_weather_v3)
- TTL: 30분

## 날씨 테마
→ frontend/app/page.tsx의 WEATHER_THEME_CLASSES 참조
- sunny: warm gradient / rainy: gray-blue / cloudy: soft gray / snowy: white-blue

## 날씨 관련 변경 시 체크리스트
1. 캐시 키 변경 시 → constants.ts 버전업 (v3→v4 등)
2. 새 날씨 조건 추가 시 → weather_scores JSONB, 테마 CSS, WeatherBanner 모두 수정
3. 빌드 확인
```

### 3-6. .claude/skills/database.md

```markdown
# 데이터베이스

## 핵심 파일
→ backend/app/models/ (8개 모델)
→ backend/app/database.py (SQLAlchemy engine)
→ data/DB_RESTORE_GUIDE.md

## movies 테이블 (22컬럼, 42,917행)
→ backend/app/models/movie.py 참조
- JSONB 3종: mbti_scores(16종), weather_scores(4종), emotion_tags(7종)
- GIN 인덱스: mbti_scores, weather_scores, emotion_tags

## 연결 테이블
→ 각 모델 파일 참조
- movie_genres(98,767), movie_cast(252,662), movie_keywords(77,660)
- similar_movies(429,170, 자기참조 M:M)

## N+1 방지
→ recommendations.py의 selectinload(Movie.genres) 참조 (4곳 적용됨)

## 스키마 변경 시 체크리스트
1. models/ 수정
2. schemas/ Pydantic 스키마 동기화
3. JSONB 인덱스 확인 (GIN)
4. 마이그레이션 스크립트 작성
5. 로컬 테스트 → pg_dump → Railway pg_restore
6. CLAUDE.md DB 모델 섹션 업데이트
7. 빌드 확인
```

### 3-7. .claude/skills/deployment.md

```markdown
# 배포

## 핵심 파일
→ DEPLOYMENT.md (상세 배포 가이드)
→ backend/railway.toml
→ frontend/vercel.json

## 환경변수
→ backend/.env.example, frontend/.env.example 참조

## 배포 프로세스
- main 브랜치 push → Railway/Vercel 자동 배포
- CORS: backend config.py의 CORS_ORIGINS에 도메인 추가

## DB 마이그레이션
→ DEPLOYMENT.md의 마이그레이션 섹션 참조
- 로컬: pg_dump → Railway: pg_restore

## 배포 시 체크리스트
1. 로컬 빌드 성공 확인
2. 환경변수 누락 확인
3. CORS_ORIGINS 확인
4. git push → 자동 배포
5. /health 엔드포인트 확인
6. 프론트엔드 주요 기능 수동 확인
```

### 3-8. .claude/skills/frontend-patterns.md

```markdown
# 프론트엔드 패턴

## 핵심 파일
→ frontend/stores/ (Zustand 2개: authStore, interactionStore)
→ frontend/hooks/ (useWeather, useInfiniteScroll, useDebounce)
→ frontend/lib/api.ts (24개 API 함수, fetchAPI 래퍼)
→ frontend/lib/constants.ts (캐시 키, 매직넘버)

## 데이터 흐름
→ frontend/app/page.tsx 참조
사용자 방문 → useWeather(Geolocation) → buildUserContext → getHomeRecommendations → 큐레이션 문구 매칭 → MovieRow 렌더링

## Zustand 패턴
→ interactionStore.ts 참조 (Optimistic UI)
→ authStore.ts 참조 (로그인/로그아웃)

## 컴포넌트 규칙
- 모듈 레벨 mutable 변수 금지 → useRef/useState 사용
- 상수는 constants.ts에 관리
- 캐시 키 변경 시 버전업

## 새 페이지 추가 시 체크리스트
1. app/경로/page.tsx 생성
2. 필요 시 layout.tsx (OG 메타태그)
3. Header.tsx 네비게이션 링크 추가
4. MobileNav.tsx 링크 추가
5. types/index.ts 타입 추가
6. lib/api.ts API 함수 추가
7. 빌드 확인
```

---

=== 4단계: .claude/settings.json ===

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic/context7-mcp"]
    }
  }
}
```

---

=== 5단계: 기존 문서 정리 ===

PROGRESS.md, CHANGELOG.md, PROJECT_CONTEXT.md, README.md, DEPLOYMENT.md는 건드리지 말 것.
이들은 기존대로 유지하되, CLAUDE.md에서 적절히 참조만 한다.

---

=== 건드리지 말 것 ===
- 모든 소스 코드 파일 (*.py, *.tsx, *.ts) — 이번 작업은 문서/설정만
- PROGRESS.md, CHANGELOG.md, PROJECT_CONTEXT.md, README.md, DEPLOYMENT.md
- backend/.env, frontend/.env.local
- data/ 디렉토리
- node_modules/, __pycache__/

---

=== 검증 ===
- 생성된 모든 .md 파일이 존재하는지 ls로 확인
- CLAUDE.md가 500줄 이하인지 확인: `wc -l CLAUDE.md`
- .claude/skills/ 디렉토리에 INDEX.md + 7개 스킬 파일 존재 확인

---

결과를 claude_results.md에 저장. 아래 형식으로:

```markdown
# 프로젝트 컨텍스트 환경 구축 결과

## 날짜
YYYY-MM-DD

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| CLAUDE.md | 프로젝트 헌법 (AI 에이전트 진입점) | N줄 |
| DECISION.md | 아키텍처 의사결정 기록 | N줄 |
| .claude/skills/INDEX.md | 스킬 목차 | N줄 |
| .claude/skills/workflow.md | RPI 프로세스, 디버깅, 컨텍스트 관리 | N줄 |
| .claude/skills/recommendation.md | 추천 엔진 도메인 지식 | N줄 |
| .claude/skills/curation.md | 큐레이션 문구 시스템 | N줄 |
| .claude/skills/weather.md | 날씨 서비스 | N줄 |
| .claude/skills/database.md | DB 스키마, 마이그레이션 | N줄 |
| .claude/skills/deployment.md | 배포 가이드 | N줄 |
| .claude/skills/frontend-patterns.md | 컴포넌트/훅/스토어 패턴 | N줄 |
| .claude/settings.json | MCP 서버 설정 | N줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| (기존 CLAUDE.md가 있었다면) | 플레이북 표준으로 재작성 |

## 핵심 변경사항
- CLAUDE.md: 플레이북 표준 형식 적용 (기술스택, 핵심 구조, DB 모델, 규칙, 스킬 참조)
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
- CLAUDE.md: N줄 (500줄 이하 ✅)
- .claude/skills/: N개 파일 존재 ✅
- 소스 코드 변경: 없음 ✅
```

git add -A && git commit -m 'docs: 프로젝트 컨텍스트 환경 구축 (CLAUDE.md, DECISION.md, skills)' && git push origin HEAD:main