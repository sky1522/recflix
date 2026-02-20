claude "Phase 37: LLM 추천 이유 생성 — Research + 설계.

=== Research ===
먼저 다음 파일들을 읽을 것:
- CLAUDE.md
- backend/app/services/llm.py (기존 Claude API 호출 + Redis 캐싱 패턴)
- backend/app/api/v1/recommendation_engine.py (RecommendationTag 구조, 추천 태그 생성)
- backend/app/api/v1/recommendations.py (추천 응답 구조)
- backend/app/api/v1/movies.py (semantic-search 응답 구조, match_reason)
- backend/app/core/config.py (ANTHROPIC_API_KEY 등)
- frontend/components/home/MovieRow.tsx 또는 HybridMovieRow.tsx (추천 카드 UI)
- frontend/components/movies/MovieCard.tsx (영화 카드 컴포넌트)

=== 설계 목표 ===
추천된 영화에 '이 영화를 추천하는 이유'를 1~2문장으로 자연스럽게 보여주기.

예시:
- '비 오는 날 잔잔한 드라마를 좋아하시는 분께 딱 맞는 힐링 영화예요'
- 'INTJ 유형이 좋아하는 지적 스릴러, 반전이 인상적입니다'
- '최근 찜한 영화와 비슷한 감성의 가족 영화입니다'

=== 설계 산출물 (claude_results.md에 덮어쓰기) ===

1. 추천 이유 생성 방식 결정
   - 옵션 A: LLM(Claude)으로 매번 생성 (비용 높음, 품질 높음)
   - 옵션 B: 템플릿 기반 생성 (비용 0, 즉시 응답, 일관성)
   - 옵션 C: 하이브리드 — 기본은 템플릿, 특별한 경우만 LLM
   - 각 방식의 장단점 + RecFlix에 최적인 방식 선택

2. 템플릿 기반이면:
   - RecommendationTag의 type별 (mbti, weather, mood, personal, similar, quality, serendipity) 한국어 문장 템플릿
   - 영화 데이터(장르, 평점, emotion_tags)를 활용한 동적 문장 조합
   - 예시 30개 이상

3. LLM 기반이면:
   - 프롬프트 설계
   - 캐싱 전략 (Redis, TTL)
   - 비용 예측
   - 폴백 (LLM 실패 시 템플릿)

4. 적용 위치
   - Backend: 추천 응답에 reason 필드 추가
   - Frontend: 어디에 어떻게 표시할지 (카드 하단? 호버? 별도 섹션?)

5. 구현 계획
   - 수정할 파일 목록
   - 단계별 실행 순서

=== 규칙 ===
- 코드 수정 하지 말 것. 설계 문서만 작성.
- 기존 추천 로직/다양성 정책 수정 금지
- 비용 효율성 최우선 (무료 또는 최소 비용)
- 기존 캐치프레이즈(llm.py) 인프라 최대 재활용

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기)"