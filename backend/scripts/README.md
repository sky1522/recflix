# RecFlix Batch Scripts

배치 스크립트 목록 및 실행 가이드.

## 실행 환경

```bash
cd backend
# Windows: ./venv/Scripts/python.exe
# Linux:   python (또는 venv 활성화 후)
```

## 필수 환경변수

| 변수 | 용도 | 스크립트 |
|------|------|----------|
| `DATABASE_URL` | PostgreSQL 연결 | 전체 |
| `TMDB_API_KEY` | TMDB Bearer Token | collect_trailers |
| `ANTHROPIC_API_KEY` | Claude API | llm_emotion_tags |
| `VOYAGE_API_KEY` | Voyage AI 임베딩 | generate_embeddings |

## 스크립트 목록

### 데이터 수집/갱신

| 스크립트 | 설명 | 실행 시간 | 권장 주기 |
|----------|------|----------|----------|
| `collect_trailers.py` | TMDB에서 YouTube 트레일러 키 수집 | ~35분 (전체) | 월 1회 |
| `generate_embeddings.py` | Voyage AI 영화 임베딩 생성 | ~1시간 | 신작 추가 시 |
| `llm_emotion_tags.py` | Claude API 감성 태그 분석 | API 비용 발생 | 신작 추가 시 |
| `regenerate_emotion_tags.py` | 키워드 기반 감성 태그 (무료) | ~5분 | llm 대안 |

### 유사도 계산

| 스크립트 | 설명 | 실행 시간 | 권장 주기 |
|----------|------|----------|----------|
| `compute_similar_movies.py` | 영화별 Top 10 유사 영화 | ~3분 | 월 1회 |
| `train_cf_model.py` | SVD 협업 필터링 모델 학습 | ~5분 | 평점 축적 시 |

### 데이터 처리

| 스크립트 | 설명 | 비고 |
|----------|------|------|
| `import_csv_data.py` | CSV → DB 초기 임포트 | 초기 1회 |
| `import_relationships.py` | 장르/키워드/출연진 관계 임포트 | 초기 1회 |
| `transliterate_cast_names.py` | 출연진 이름 한글 음역 | 초기 1회 |
| `transliterate_persons.py` | persons 테이블 한글화 | 초기 1회 |

### DB 마이그레이션

| 스크립트 | 설명 |
|----------|------|
| `migrate_trailer.sql` | trailer_key 컬럼 추가 |
| `migrate_search_index.sql` | pg_trgm 검색 인덱스 |
| `migrate_phase4.sql` | Phase 4 스키마 변경 |
| `migrate_add_columns.py` | 신규 컬럼 추가 |

## 주요 스크립트 실행 예시

```bash
# 트레일러 수집 (전체)
python scripts/collect_trailers.py

# 트레일러 수집 (테스트 100개, DB 저장 없음)
python scripts/collect_trailers.py --limit 100 --dry-run

# 유사 영화 계산 (미리보기)
python scripts/compute_similar_movies.py --dry-run

# 유사 영화 계산 (전체 + DB 저장)
python scripts/compute_similar_movies.py

# SVD 모델 학습
python scripts/train_cf_model.py
```

## 정기 갱신 체크리스트 (월 1회)

1. `collect_trailers.py` — 신작 트레일러 수집
2. `compute_similar_movies.py` — 유사 영화 재계산
3. (선택) `regenerate_emotion_tags.py` — 감성 태그 없는 신작 처리
