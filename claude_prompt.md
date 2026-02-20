claude "Phase 37: LLM 추천 이유 생성 — 템플릿 기반 구현.

=== Research ===
먼저 다음 파일들을 읽고 현재 구조를 파악할 것:
- CLAUDE.md
- backend/app/api/v1/recommendation_engine.py (calculate_hybrid_scores 반환 형식, RecommendationTag 구조)
- backend/app/api/v1/recommendations.py (추천 응답 조립 방식, HybridMovieItem 사용법)
- backend/app/schemas/recommendation.py (HybridMovieItem, from_movie_with_tags 등)
- backend/app/api/v1/recommendation_constants.py (MBTI/날씨/기분 매핑)
- frontend/types/index.ts (HybridMovie 인터페이스)
- frontend/components/movie/HybridMovieCard.tsx 또는 MovieCard 관련 컴포넌트 (추천 카드 UI)

=== 1단계: recommendation_reason.py 생성 ===
backend/app/api/v1/recommendation_reason.py 신규 생성:

generate_reason(tags, movie, mbti, weather, mood) → str 함수:

1. 태그 우선순위: 복합조건 > Mood/Personal > MBTI > Weather > Quality
2. 동적 변수: {mbti}, {genre}, {vote_avg}, {weather_ko}, {mood_ko}
3. 템플릿 매칭 로직:
   - tags에서 type별 태그 추출
   - 복합 조건 먼저 체크 (mbti+weather, mbti+mood, weather+mood, personal+quality)
   - 매칭되면 해당 템플릿 반환
   - 안 되면 단일 태그 우선순위대로 체크
   - 아무것도 매칭 안 되면 기본 폴백: '추천 영화예요'

날씨 한국어 매핑: sunny→맑은 날, rainy→비 오는 날, cloudy→흐린 날, snowy→눈 오는 날
기분 한국어 매핑: relaxed→편안한, tense→긴장감 넘치는, energetic→신나는, romantic→감성적인, thoughtful→깊은 생각에 잠기는, adventurous→모험적인, melancholy→울적한, playful→가벼운
(실제 mood 값은 recommendation_constants.py에서 확인 후 맞출 것)

MBTI 기질 매핑: NT→논리와 분석, NF→감성과 공감, SJ→안정과 질서, SP→즉흥적이고 활동적인

설계 문서의 43개 템플릿을 모두 포함.
같은 조건에 여러 템플릿이 있으면 random.choice로 다양성 확보.

=== 2단계: 스키마 수정 ===
backend/app/schemas/recommendation.py:
- HybridMovieItem에 recommendation_reason: str = '' 필드 추가

=== 3단계: 추천 엔진/API 연동 ===
recommendation_engine.py 또는 recommendations.py에서:
- 추천 결과 조립 시 generate_reason() 호출
- tags, movie, mbti, weather, mood를 전달
- 반환된 reason을 HybridMovieItem.recommendation_reason에 설정
- 실제 반환 형식에 맞게 적용 (from_movie_with_tags가 있으면 거기에, 아니면 응답 조립 시)

⚠️ calculate_hybrid_scores의 실제 반환 형식을 먼저 확인하고 그에 맞게 적용.
⚠️ 기존 추천 로직/다양성 정책 수정 금지.

=== 4단계: Frontend 타입 수정 ===
frontend/types/index.ts:
- HybridMovie 인터페이스에 recommendation_reason?: string 추가

=== 5단계: Frontend UI 표시 ===
HybridMovieCard.tsx (또는 추천 영화 카드 컴포넌트):
- recommendation_reason이 있으면 태그 뱃지 아래에 표시
- 스타일: text-xs text-white/50 italic line-clamp-2
- 최대 2줄, 넘치면 ... 처리
- recommendation_reason이 없거나 빈 문자열이면 표시 안 함

=== 규칙 ===
- 기존 추천 로직 (가중치, 다양성, CF) 수정 금지
- LLM API 호출 없음 — 순수 템플릿 기반
- recommendation_reason.py는 100~150줄 이내
- 모든 함수에 타입 힌트 + docstring
- .md 문서 파일 건드리지 말 것

=== 검증 ===
1. cd backend && ruff check app/api/v1/recommendation_reason.py
2. cd backend && python -c 'from app.api.v1.recommendation_reason import generate_reason; print(generate_reason([], None, \"INTJ\", \"rainy\", \"relaxed\"))'
   → 빈 문자열이 아닌 추천 이유 문장 출력
3. 로컬 서버 시작 후:
   curl 'http://localhost:8000/api/v1/recommendations?weather=rainy&mood=relaxed&limit=5'
   → 각 영화에 recommendation_reason 필드가 포함되어 있는지 확인
4. cd frontend && npm run build — 빌드 성공
5. git add -A && git commit -m 'feat: Phase 37 추천 이유 생성 (템플릿 기반, 43개 패턴)' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 생성/수정된 파일 목록
- generate_reason 테스트 결과 (3개 이상 다른 컨텍스트)
- API 응답 예시 (recommendation_reason 포함)
- Frontend UI 동작 설명
- 프로덕션 배포 필요 여부"