# RecFlix Architecture Decisions

## 1. 추천 엔진: Rule-based Hybrid Scoring

- **현황**: MBTI/날씨/기분/개인화 4축 하이브리드 (`recommendations.py` 770 LOC)
- **결정**: ML 모델 대신 Rule-based 가중치 스코어링 채택
- **근거**: 42,917편 규모에서 실시간 응답 필요, 학습 데이터 부족, 가중치 직관적 튜닝 가능
- **대안 검토**: 협업 필터링 (사용자 수 부족으로 기각), 콘텐츠 기반 추천 (JSONB 스코어로 대체)
- **가중치**: Mood시 0.25/0.20/0.30/0.25 (MBTI/Weather/Mood/Personal), Mood 없이 0.35/0.25/0.40
- **품질 보정**: weighted_score 기반 x0.85~1.0 연속 보정, 최소 필터 >= 6.0

## 2. emotion_tags: 2-Tier 시스템 (LLM + 키워드)

- **현황**: 7대 감성 클러스터 (healing, tension, energy, romance, deep, fantasy, light)
- **결정**: 상위 1,711편은 Claude API(claude-sonnet-4-20250514) 분석, 나머지 41,206편은 키워드 기반 생성
- **근거**: 전체 LLM 분석 비용 과다, 키워드 기반 0.7 상한으로 품질 차등
- **LLM 분석**: emotion_tags 값 <= 1.0, 세밀한 분포 (0.35, 0.72 등)
- **키워드 기반**: score = min(base_score + genre_boost - penalty, 0.7)
- **스크립트**: `backend/scripts/llm_emotion_tags.py`, `backend/scripts/regenerate_emotion_tags.py`

## 3. 유사 영화: 자체 계산

- **결정**: TMDB 유사 영화 대신 자체 코사인 유사도 사용
- **공식**: 0.5 x emotion코사인 + 0.3 x mbti코사인 + 0.2 x 장르Jaccard + LLM보너스(0.05)
- **근거**: RecFlix 자체 점수 체계와 일관된 추천, TMDB 유사도는 장르만 고려
- **규모**: 42,917편 x Top 10 = 429,170개 관계, weighted_score >= 6.0 필터
- **스크립트**: `backend/scripts/compute_similar_movies.py` (~40분 소요)

## 4. cast_ko 한글화: Claude API 음역

- **결정**: 42,759편 출연진 이름 100% 한글화
- **방법**: Claude API로 4,253개 외국어 이름 음역 ($1.78)
  - 중국어 1,902 / 영어 1,902 / 일본어 139 / 악센트 라틴 187 / 키릴 64 / 그리스어 11
- **근거**: 한국 사용자 UX, 검색 편의성
- **구조**: `movies.cast_ko` (쉼표 구분 문자열) → 프론트엔드에서 `.split(", ")` 파싱
- **스크립트**: `backend/scripts/transliterate_cast_names.py`

## 5. 프론트엔드 상태관리: Zustand

- **결정**: Redux/Recoil 대신 Zustand 채택
- **근거**: 보일러플레이트 최소, 러닝커브 낮음, 2개 스토어로 충분
- **스토어**: `authStore` (인증), `interactionStore` (찜/평점 Optimistic UI)
- **패턴**: persist middleware로 토큰 영속화, Optimistic UI로 즉시 반영

## 6. 배포: Vercel + Railway

- **결정**: Frontend=Vercel, Backend+DB+Redis=Railway
- **근거**: Next.js SSR 최적화(Vercel), PostgreSQL+Redis 통합 관리(Railway)
- **CORS**: `config.py`의 `CORS_ORIGINS`에 Vercel 도메인 등록
- **DB 마이그레이션**: 로컬 pg_dump → Railway pg_restore

## 7. 큐레이션 문구: 정적 258개 시스템

- **결정**: LLM 실시간 생성 대신 사전 정의 258개 문구
- **근거**: 응답 속도, 비용 절약, 품질 일관성
- **구조**: 시간대(24) + 계절(24) + 기온(24) + 날씨(24) + 기분(48) + MBTI(96) + 고정(18) = 258개
- **컨텍스트 감지**: 시간대(getHours), 계절(getMonth), 기온(weather.temperature)
- **파일**: `frontend/lib/curationMessages.ts`, `frontend/lib/contextCuration.ts`
