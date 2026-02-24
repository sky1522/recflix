# 데이터베이스

## 핵심 파일
→ `backend/app/models/` (9개 모델: movie, user, rating, collection, similar_movie, user_event + __init__)
→ `backend/app/database.py` (SQLAlchemy engine)
→ `data/DB_RESTORE_GUIDE.md`

## movies 테이블 (22컬럼, 42,917행)
→ `backend/app/models/movie.py` 참조

### 컬럼 구조
- 기본 정보 (13): id(TMDB PK), title, title_ko, certification, runtime, vote_average, vote_count, popularity, overview, tagline, poster_path, release_date, is_adult
- 추가 정보 (6): director, director_ko, cast_ko, production_countries_ko, release_season, weighted_score
- 점수 JSONB (3): mbti_scores(16종), weather_scores(4종), emotion_tags(7종)

### GIN 인덱스
```sql
CREATE INDEX idx_movies_mbti ON movies USING GIN(mbti_scores);
CREATE INDEX idx_movies_weather ON movies USING GIN(weather_scores);
CREATE INDEX idx_movies_emotion ON movies USING GIN(emotion_tags);
```

## 연결 테이블
→ 각 모델 파일 참조
- movie_genres (98,767행): Movie ↔ Genre (19종)
- movie_cast (252,662행): Movie ↔ Person (97,206명)
- movie_keywords (77,660행): Movie ↔ Keyword
- similar_movies (429,170행): 자기참조 M:M, 영화별 Top 10

## N+1 방지
→ `recommendations.py`의 `selectinload(Movie.genres)` 참조 (4곳 적용됨)

## CSV → DB 컬럼 매핑 (주의)
- CSV `title`(한국어) → DB `title_ko`
- CSV `title_ko_en`(영어) → DB `title`
- CSV `overview`(한국어 통일) → DB `overview`

## DB 마이그레이션 (로컬 → Railway)
```bash
# 로컬 덤프
PGPASSWORD=recflix123 pg_dump -h localhost -U recflix -d recflix --no-owner --no-acl -Fc -f dump.dump

# Railway 복원
PGPASSWORD=<railway_pw> pg_restore -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway --clean --if-exists --no-owner --no-acl dump.dump
```

## users 테이블 (17컬럼)
→ `backend/app/models/user.py` 참조
- 인증: id, email(UNIQUE), hashed_password, mbti, created_at, updated_at
- 소셜 로그인: kakao_id, google_id, auth_provider(default 'local'), profile_image
- 개인화: onboarding_completed(default false), preferred_genres(TEXT)
- A/B 테스트: experiment_group

## user_events 테이블 (Phase 30, 프로덕션 적용 완료)
→ `backend/app/models/user_event.py` 참조
- 10종 이벤트: page_view, movie_click, search, filter, rating, collection, recommendation_click, scroll, impression, ab_assignment
- 컬럼: id, user_id(nullable), event_type, event_data(JSONB), session_id, created_at, page_url
- 인덱스: user_id, event_type, created_at, session_id, (event_type+created_at)

## trailer_key (Phase 47)
→ movies 테이블에 `trailer_key` 컬럼 추가 (YouTube video ID)
→ 28,486/42,917편 (66.4%) 커버
→ `collect_trailers.py` 스크립트로 TMDB API 수집

## Alembic 마이그레이션 (Phase 48)
→ `backend/alembic/` 디렉토리
→ `Base.metadata.create_all()` 제거, Alembic 관리로 전환
→ 초기 마이그레이션은 빈 baseline (stamp head)
→ env.py: settings.DATABASE_URL 동적 설정

## 스키마 변경 시 체크리스트
1. `models/` 수정
2. `schemas/` Pydantic 스키마 동기화
3. JSONB 인덱스 확인 (GIN)
4. `alembic revision --autogenerate -m "설명"` (Alembic 마이그레이션)
5. `alembic upgrade head` (로컬 적용)
6. 로컬 테스트 → pg_dump → Railway pg_restore
7. CLAUDE.md DB 모델 섹션 업데이트
8. 빌드 확인
