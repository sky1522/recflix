# 프롬프트 1: recommendations.py 리팩토링 (770줄 → 500줄 이하)

핵심 비즈니스 로직 리팩토링. 기능 변경 없이 구조만 분리. 충분히 탐색하고 시작해.

먼저 읽을 것:
- .claude/skills/code-quality.md (파일 크기 규칙, 분리 기준)
- .claude/skills/recommendation.md (추천 엔진 도메인 지식)
- backend/app/api/v1/recommendations.py (전체 구조 파악 — 770줄이므로 grep으로 함수 목록부터)

```bash
# 함수 목록 확인
grep -n "^def \|^async def " backend/app/api/v1/recommendations.py

# calculate_hybrid_scores 범위 확인
grep -n "calculate_hybrid_scores\|def _calc" backend/app/api/v1/recommendations.py

# 상수/매핑 확인
grep -n "MOOD_EMOTION_MAP\|AGE_RATING_MAP\|WEATHER_\|MBTI_" backend/app/api/v1/recommendations.py

# import 확인
head -30 backend/app/api/v1/recommendations.py
```

---

=== 1단계: Research ===

recommendations.py의 구조를 파악하고 분리 계획을 세워줘:

1. 모든 함수와 줄 범위 정리
2. 상수/매핑 데이터 위치 파악 (MOOD_EMOTION_MAP, AGE_RATING_MAP 등)
3. calculate_hybrid_scores() 내부 로직 파악 (133줄 중 어디서 나눌 수 있는지)
4. 함수 간 의존관계 확인 (어떤 함수가 어떤 함수를 호출하는지)

---

=== 2단계: Plan ===

아래 분리 방향을 기반으로 구체적 계획 수립:

**새 파일 생성:**
- `backend/app/api/v1/recommendation_engine.py` — 순수 계산 로직
  - `calculate_mbti_score(movie, mbti)` 
  - `calculate_weather_score(movie, weather)`
  - `calculate_mood_score(movie, mood, mood_emotion_map)`
  - `calculate_personal_score(movie, user_genres, similar_ids, ...)`
  - `calculate_hybrid_scores(movies, ...)` → 위 4개를 조합하는 오케스트레이터
  - 추천 태그 부여 함수
  - 품질 보정 함수

- `backend/app/api/v1/recommendation_constants.py` — 상수/매핑
  - MOOD_EMOTION_MAP
  - AGE_RATING_MAP  
  - 날씨/MBTI 매핑 상수
  - 가중치 상수 (WEIGHTS_WITH_MOOD, WEIGHTS_WITHOUT_MOOD 등)

**기존 파일 수정:**
- `backend/app/api/v1/recommendations.py` — API 라우터만 남김
  - 엔드포인트 함수들 (DB 쿼리 + engine 호출 + 응답 반환)
  - import 추가

**목표:** recommendations.py 500줄 이하, recommendation_engine.py 300줄 이하, recommendation_constants.py 100줄 이하

실제 코드를 확인한 후 이 계획을 조정해줘. 무리하게 나누지 말고, 자연스러운 경계에서 분리.

---

=== 3단계: Implement ===

계획대로 구현. 주의사항:

1. **기능 변경 절대 금지** — 순수 리팩토링만
2. 모든 import 경로 정확히 (router.py에서 recommendations를 import하는 부분 확인)
3. 타입 힌트 유지/보강
4. selectinload 등 기존 최적화 유지
5. 기존 테스트가 없으므로, 수동 검증:
   - `cd backend && python -c "from app.api.v1 import recommendations; print('OK')"`
   - `cd backend && python -c "from app.api.v1.recommendation_engine import calculate_hybrid_scores; print('OK')"`
   - `ruff check backend/app/api/v1/recommendation*.py`

---

=== 건드리지 말 것 ===
- frontend/ 전체
- backend/app/api/v1/ 중 recommendations.py 외 다른 라우터 파일
- backend/app/models/, schemas/, services/
- backend/app/core/
- 모든 .md 문서 파일 (CLAUDE.md, 스킬 등은 나중에 별도 업데이트)
- backend/.env

---

=== 검증 ===
```bash
# 파일별 줄 수 확인
wc -l backend/app/api/v1/recommendation*.py

# Python 파싱 확인
python -c "import ast; ast.parse(open('backend/app/api/v1/recommendations.py').read()); print('recommendations.py OK')"
python -c "import ast; ast.parse(open('backend/app/api/v1/recommendation_engine.py').read()); print('engine OK')"
python -c "import ast; ast.parse(open('backend/app/api/v1/recommendation_constants.py').read()); print('constants OK')"

# import 확인
cd backend && python -c "from app.api.v1.recommendations import router; print('router OK')"

# Ruff 린트
ruff check backend/app/api/v1/recommendation*.py
```

---

결과를 claude_results.md에 **기존 내용 아래에 --- 구분선 후 이어서** 저장:

```markdown
---

# recommendations.py 리팩토링 결과

## 날짜
YYYY-MM-DD

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| recommendation_engine.py | 순수 계산 로직 (스코어링, 태그, 보정) | N줄 |
| recommendation_constants.py | 상수/매핑 데이터 | N줄 |

## 수정된 파일
| 파일 | 변경 내용 | 줄 수 변화 |
|------|----------|-----------|
| recommendations.py | API 라우터만 남김, engine/constants import | 770줄 → N줄 |

## 분리 결과
| 파일 | 줄 수 | 역할 |
|------|-------|------|
| recommendations.py | N줄 | API 엔드포인트 (DB 쿼리 + 응답) |
| recommendation_engine.py | N줄 | 하이브리드 스코어링 (순수 계산) |
| recommendation_constants.py | N줄 | 매핑/가중치 상수 |
| **합계** | N줄 | (770줄에서 변화) |

## 검증 결과
- Python AST: 3개 파일 모두 OK ✅
- Import: router OK ✅
- Ruff: No errors ✅
- 기능 변경: 없음 ✅
```

git add -A && git commit -m 'refactor(backend): recommendations.py 모듈 분리 (engine, constants)' && git push origin HEAD:main