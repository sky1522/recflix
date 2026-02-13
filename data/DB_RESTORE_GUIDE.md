# RecFlix DB 복원 가이드

## 파일 정보
- **파일**: `recflix_db.dump` (22MB, PostgreSQL custom format)
- **영화 수**: 42,917편
- **cast_ko 한글화율**: 100% (42,759/42,759편)
- **LLM 감성 분석**: 1,711편 (Claude Sonnet)
- **키워드 기반 감성**: 41,206편
- **생성일**: 2026-02-13

## 포함된 데이터
| 테이블 | 설명 |
|--------|------|
| movies | 42,917편 (22컬럼: 기본정보 + emotion_tags, mbti_scores, weather_scores 등) |
| genres | 장르 마스터 |
| movie_genres | 영화-장르 매핑 |
| persons | 배우 97,206명 (프론트엔드 미사용, cast_ko 사용) |
| cast_members | 영화-배우 매핑 |
| similar_movies | 유사 영화 매핑 |
| keywords, movie_keywords | 키워드 마스터 및 매핑 |
| users, collections, ratings | 사용자 관련 (빈 데이터) |

## 복원 방법

### 1. PostgreSQL 설치 (없는 경우)
```bash
# macOS
brew install postgresql@16

# Ubuntu/Debian
sudo apt install postgresql-16

# Windows
# https://www.postgresql.org/download/windows/ 에서 설치
```

### 2. DB 생성
```bash
# PostgreSQL 접속
psql -U postgres

# DB 및 유저 생성
CREATE USER recflix WITH PASSWORD 'recflix123';
CREATE DATABASE recflix OWNER recflix;
\q
```

### 3. 복원
```bash
# macOS/Linux
PGPASSWORD=recflix123 pg_restore -h localhost -U recflix -d recflix \
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump

# Windows (Git Bash)
PGPASSWORD=recflix123 "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" \
  -h localhost -U recflix -d recflix \
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump
```

### 4. 확인
```bash
PGPASSWORD=recflix123 psql -h localhost -U recflix -d recflix -c "
  SELECT COUNT(*) as total_movies,
         COUNT(cast_ko) as with_cast_ko,
         COUNT(*) FILTER (WHERE emotion_tags IS NOT NULL) as with_tags
  FROM movies;"
```

예상 결과:
```
 total_movies | with_cast_ko | with_tags
--------------+--------------+-----------
        42917 |        42759 |     42917
```

## DB 스키마 (movies 테이블 - 22컬럼)

### 기본 정보 (13컬럼)
```
id                        - TMDB 영화 ID
title                     - 영문 제목
title_ko                  - 한글 제목
overview                  - 줄거리 (한국어)
certification             - 등급 (ALL, 12, 15, 19, R 등)
runtime                   - 상영시간 (분)
vote_average, vote_count  - TMDB 평점/투표수
popularity                - TMDB 인기도
poster_path               - 포스터 이미지 경로 (TMDB)
release_date              - 개봉일
tagline                   - 태그라인
is_adult                  - 성인 여부
```

### 추가 정보 (6컬럼)
```
director / director_ko    - 감독 (영문/한글)
cast_ko                   - 출연진 (한글, 콤마 구분, 100% 한글화)
production_countries_ko   - 제작국가 (한글)
release_season            - 개봉 시즌 (spring/summer/fall/winter)
weighted_score            - 가중 평점 (vote_count 반영, 품질 필터용)
```

### 추천 점수 (3컬럼, JSONB)
```
emotion_tags (JSONB)      - 7대 감성 클러스터 점수 (0.0~1.0)
  → healing, tension, energy, romance, deep, fantasy, light
mbti_scores (JSONB)       - 16개 MBTI 유형별 점수
  → INTJ, INTP, ENTJ, ENTP, INFJ, INFP, ENFJ, ENFP, ...
weather_scores (JSONB)    - 4개 날씨별 점수
  → sunny, rainy, cloudy, snowy
```

### emotion_tags 품질 구분
| 분석 방식 | 영화 수 | 최대 점수 | 특징 |
|----------|---------|----------|------|
| LLM (Claude Sonnet) | 1,711 | 1.0 | 세밀한 소수점 (0.35, 0.72 등) |
| 키워드 기반 | 41,206 | 0.7 | 장르/줄거리 키워드 매칭 |

## Backend 연동
`.env` 파일에 DATABASE_URL 설정:
```
DATABASE_URL=postgresql://recflix:recflix123@localhost:5432/recflix
```

## Redis 설치 (추천 캐싱용)
```bash
# macOS
brew install redis

# Windows - Memurai 설치
# https://www.memurai.com/get-memurai

# .env 설정
REDIS_URL=redis://:recflix123@localhost:6379/0
```

## 문의
- GitHub: https://github.com/sky1522/recflix
