# 임베딩 기반 자연어 영화 탐색 — 설계 문서

**작성일**: 2026-02-20
**목표**: "오늘 비오는데 혼자 보기 좋은 잔잔한 영화" 같은 자연어 쿼리로 영화를 검색하는 시맨틱 검색 기능

---

## 1. pgvector 사용 가능 여부

### 조사 결과: **사용 불가**

```sql
-- Railway PostgreSQL 17.7 (Debian 17.7-3.pgdg13+1)
SELECT name FROM pg_available_extensions WHERE name = 'vector';
-- (0 rows)
```

Railway PostgreSQL에서 pgvector 확장은 제공되지 않는다. 사용 가능한 관련 확장:
- `pg_trgm` 1.6 (문자열 유사도, 이미 활용 가능)
- `fuzzystrmatch` 1.2 (음성 유사도)
- `hstore` 1.8, `unaccent` 1.1

### 대안 선택: **NumPy 인메모리 벡터 검색**

| 대안 | 장점 | 단점 | 적합도 |
|------|------|------|--------|
| **NumPy 인메모리** | 의존성 0, 10-20ms 검색, 이미 설치됨 | 서버 재시작 시 재로드 필요 | **최적** |
| FAISS | SIMD 최적화, 대규모 지원 | 42K에 과잉, 추가 의존성 | 향후 확장 시 |
| ChromaDB | 메타데이터 필터링 내장 | 200-400MB RAM, 추가 서비스 | 과잉 |
| Qdrant | 프로덕션급 벡터 DB | 별도 Railway 서비스 필요 ($5/월) | 과잉 |
| Pinecone | 무료 10만 벡터 | 네트워크 레이턴시, 외부 의존 | 대안 |

**선택 근거**: 42,917편 × 1,024차원 = **~176MB** — NumPy로 충분. brute-force 코사인 유사도 검색이 10-20ms이므로 인덱스 불필요.

---

## 2. 임베딩 모델 선택

### 비교표

| 모델 | 차원 | 비용 (42,917편) | 쿼리 비용 | 한국어 품질 | 로컬/API | Railway 적합 |
|------|------|----------------|----------|-----------|---------|------------|
| OpenAI text-embedding-3-small | 1,536 | ~$0.06 | ~$0 | 양호 | API | O |
| jhgan/ko-sroberta-multitask | 768 | $0 | $0 | 우수 (한국어 전용) | 로컬 | △ (~1.5GB RAM) |
| intfloat/multilingual-e5-large | 1,024 | $0 | $0 | 우수 | 로컬 | △ (~2.1GB RAM) |
| **Voyage AI voyage-multilingual-2** | **1,024** | **$0 (무료 50M 토큰)** | **~$0** | **우수** | **API** | **O** |
| Cohere embed-multilingual-v3.0 | 1,024 | ~$0.30 | ~$0 | 양호 | API | O |

> Anthropic은 임베딩 API를 제공하지 않으며, Voyage AI를 공식 파트너로 권장한다.

### 선택: **Voyage AI `voyage-multilingual-2`**

**선택 이유:**
1. **비용**: 첫 50M 토큰 무료 → 42,917편 전체 임베딩 + 수년간 쿼리 트래픽 무료
2. **한국어 품질**: 27개 언어 포함, 한국어 리트리벌 벤치마크에서 OpenAI/Cohere 능가
3. **차원**: 1,024 (176MB 인메모리, Railway Hobby 충분)
4. **Anthropic 공식 파트너**: Claude 기반 시스템과 최적 호환
5. **컨텍스트**: 32,768 토큰 (긴 overview도 문제없음)
6. **Railway 메모리 부담 없음**: API 호출이므로 모델 로드 불필요

**비용 산출:**
- 42,917편 × 평균 214자(한국어) ≈ 42,917 × 70토큰 = ~3.0M 토큰
- 무료 50M 토큰 이내 → **$0**
- 쿼리당: ~70토큰 → 무료 한도 내에서 ~71만 쿼리 가능

---

## 3. 임베딩 소스 텍스트 설계

### 현재 데이터 현황

| 필드 | 커버리지 | 예시 |
|------|---------|------|
| overview (한국어) | 42,903/42,917 (99.97%) | "촉망받는 은행 간부 앤디 듀프레인은..." |
| emotion_tags (JSONB) | 42,917/42,917 (100%) | `{"deep":0.9, "healing":0.8, ...}` |
| genres | 연결 테이블 (19종) | "드라마, 범죄" |
| keywords | 34,214/42,917 (79.7%), 88종 | "사랑, 가족, 비밀" |
| mbti_scores (JSONB) | 42,917/42,917 (100%) | 16종 점수 |
| weather_scores (JSONB) | 42,917/42,917 (100%) | 4종 점수 |
| director_ko | 대부분 존재 | "프랭크 다라본트" |
| cast_ko | 100% 한글 | "팀 로빈스, 모건 프리먼" |

### 임베딩 텍스트 템플릿

```python
def build_embedding_text(movie: dict) -> str:
    """영화 데이터를 시맨틱 검색용 텍스트로 변환"""
    parts = []

    # 1. 제목 (한국어 + 영어)
    parts.append(f"제목: {movie['title_ko']}")
    if movie.get('title') and movie['title'] != movie['title_ko']:
        parts.append(f"영어 제목: {movie['title']}")

    # 2. 장르
    if movie.get('genres'):
        parts.append(f"장르: {movie['genres']}")

    # 3. 줄거리 (핵심 시맨틱 정보)
    if movie.get('overview'):
        parts.append(f"줄거리: {movie['overview'][:500]}")

    # 4. 감성 태그 (높은 점수만 자연어로 변환)
    if movie.get('emotion_tags'):
        emotion_labels = {
            'healing': '힐링/치유', 'tension': '긴장/스릴',
            'energy': '활기/에너지', 'romance': '로맨스/감성',
            'deep': '깊은/철학적', 'fantasy': '판타지/상상',
            'light': '가벼운/유쾌'
        }
        high_emotions = [
            emotion_labels[k]
            for k, v in movie['emotion_tags'].items()
            if isinstance(v, (int, float)) and v >= 0.5
        ]
        if high_emotions:
            parts.append(f"분위기: {', '.join(high_emotions)}")

    # 5. 날씨 적합도 (높은 점수만)
    if movie.get('weather_scores'):
        weather_labels = {
            'sunny': '맑은 날', 'rainy': '비 오는 날',
            'cloudy': '흐린 날', 'snowy': '눈 오는 날'
        }
        high_weather = [
            weather_labels[k]
            for k, v in movie['weather_scores'].items()
            if isinstance(v, (int, float)) and v >= 0.3
        ]
        if high_weather:
            parts.append(f"어울리는 날씨: {', '.join(high_weather)}")

    # 6. MBTI 적합도 (상위 3개)
    if movie.get('mbti_scores'):
        sorted_mbti = sorted(
            movie['mbti_scores'].items(),
            key=lambda x: float(x[1]) if x[1] else 0, reverse=True
        )[:3]
        high_mbti = [k for k, v in sorted_mbti if float(v) >= 0.2]
        if high_mbti:
            parts.append(f"MBTI 추천: {', '.join(high_mbti)}")

    # 7. 키워드
    if movie.get('keywords'):
        parts.append(f"키워드: {movie['keywords']}")

    # 8. 감독
    if movie.get('director_ko'):
        parts.append(f"감독: {movie['director_ko']}")

    return '\n'.join(parts)
```

### 예시 출력 (쇼생크 탈출, id=278)

```
제목: 쇼생크 탈출
영어 제목: The Shawshank Redemption
장르: 드라마, 범죄
줄거리: 촉망받는 은행 간부 앤디 듀프레인은 아내와 그녀의 정부를 살해했다는 누명을 쓴다. 주변의 증언과 살해 현장의 그럴듯한 증거들로 그는 종신형을 선고받고 악질범들만 수용한다는 지옥같은 교도소 쇼생크로 향한다...
분위기: 깊은/철학적, 힐링/치유, 긴장/스릴
어울리는 날씨: 비 오는 날, 흐린 날
MBTI 추천: ENTJ, INTJ, ISTJ
키워드: 정부
감독: 프랭크 다라본트
```

예상 텍스트 길이: 평균 300-500자 (한국어) → ~100-170 토큰

---

## 4. DB 스키마 변경

### pgvector 없이 벡터를 저장하는 방법

pgvector가 없으므로 벡터를 DB에 저장하지 않는다. 대신:

**파일 기반 저장**: `movie_embeddings.npy` (NumPy 바이너리)
- 크기: 42,917 × 1,024 × 4바이트 = **~176MB**
- FastAPI 시작 시 메모리에 로드
- 영화 ID → 인덱스 매핑: `movie_id_index.json`

### 마이그레이션 SQL (선택적, 메타데이터용)

```sql
-- 임베딩 생성 여부 추적용 컬럼 (선택적)
ALTER TABLE movies ADD COLUMN IF NOT EXISTS has_embedding BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_movies_has_embedding ON movies(has_embedding) WHERE has_embedding = FALSE;
```

### 파일 구조

```
backend/
  data/
    embeddings/
      movie_embeddings.npy       # (42917, 1024) float32, ~176MB
      movie_id_index.json        # {"0": 278, "1": 840464, ...} idx→movie_id
      embedding_metadata.json    # {"model": "voyage-multilingual-2", "dims": 1024, "count": 42917, "created_at": "..."}
```

---

## 5. API 설계

### 엔드포인트

```
GET /api/v1/movies/semantic-search?q=자연어쿼리&limit=20&age_rating=all
```

### 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| q | string | O | 자연어 검색 쿼리 (최소 2자) |
| limit | int | X | 반환 결과 수 (기본 20, 최대 50) |
| age_rating | string | X | 연령등급 필터 (all/family/teen/adult) |
| weather | string | X | 현재 날씨 (sunny/rainy/cloudy/snowy) — 재랭킹에 활용 |
| mood | string | X | 현재 기분 — 재랭킹에 활용 |

### 처리 흐름

```
사용자 쿼리 "비오는 날 혼자 보기 좋은 잔잔한 영화"
    │
    ▼
[1] Redis 캐시 확인 (캐시 키: semantic:{query_hash}:{params})
    │ 히트 → 즉시 반환
    │ 미스 ↓
    ▼
[2] Voyage AI API로 쿼리 임베딩 변환 (1,024차원)
    │ ~100-200ms (API 호출)
    │
    ▼
[3] NumPy 코사인 유사도 검색 (Top 100 후보)
    │ ~10-20ms (인메모리 brute-force)
    │ corpus_embeddings @ query_embedding → scores
    │ np.argpartition으로 Top 100 추출
    │
    ▼
[4] DB에서 후보 영화 조회 (100편)
    │ SELECT * FROM movies WHERE id IN (...)
    │ + genres JOIN
    │
    ▼
[5] 하이브리드 재랭킹 (기존 엔진 활용)
    │ semantic_score * 0.6 + hybrid_score * 0.4
    │ hybrid_score = f(weather, mood, mbti, personal)
    │ 품질 필터: weighted_score >= 6.0
    │
    ▼
[6] 상위 20편 반환 + Redis 캐시 저장 (TTL 30분)
```

### 응답 스키마

```python
class SemanticSearchResult(BaseModel):
    """시맨틱 검색 결과 아이템"""
    id: int
    title: str
    title_ko: str | None
    poster_path: str | None
    release_date: str | None
    weighted_score: float | None
    genres: list[str]
    semantic_score: float        # 벡터 유사도 (0~1)
    relevance_score: float       # 최종 재랭킹 점수 (0~1)
    match_reason: str            # "줄거리 유사", "분위기 일치" 등

class SemanticSearchResponse(BaseModel):
    """시맨틱 검색 응답"""
    query: str
    results: list[SemanticSearchResult]
    total: int
    search_time_ms: float
```

### 쿼리 임베딩 캐싱 전략

```python
# Redis 캐시 계층:
# 1. 쿼리 임베딩 캐시: semantic_emb:{query_hash} → 벡터(bytes), TTL 24시간
# 2. 검색 결과 캐시: semantic_res:{query_hash}:{params_hash} → JSON, TTL 30분

import hashlib

def get_query_cache_key(query: str) -> str:
    normalized = query.strip().lower()
    query_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
    return f"semantic_emb:{query_hash}"

def get_result_cache_key(query: str, limit: int, age_rating: str | None) -> str:
    normalized = query.strip().lower()
    params = f"{limit}:{age_rating or 'none'}"
    combined = f"{normalized}:{params}"
    result_hash = hashlib.md5(combined.encode()).hexdigest()[:12]
    return f"semantic_res:{result_hash}"
```

### 코드 예시 — 벡터 검색 모듈

```python
# backend/app/api/v1/semantic_search.py

import json
import logging
import time
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db
from app.core.rate_limit import limiter
from app.models import Movie
from app.services.llm import get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/movies", tags=["Movies"])

# --- 인메모리 벡터 인덱스 ---
_corpus_embeddings: np.ndarray | None = None  # (N, 1024), L2 normalized
_movie_ids: list[int] = []                     # index → movie_id 매핑

EMBEDDINGS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "embeddings"


def load_embeddings() -> None:
    """서버 시작 시 임베딩을 메모리에 로드"""
    global _corpus_embeddings, _movie_ids

    emb_path = EMBEDDINGS_DIR / "movie_embeddings.npy"
    idx_path = EMBEDDINGS_DIR / "movie_id_index.json"

    if not emb_path.exists():
        logger.warning("Embedding file not found: %s", emb_path)
        return

    _corpus_embeddings = np.load(str(emb_path)).astype(np.float32)
    # L2 정규화 (코사인 유사도 → 내적으로 변환)
    norms = np.linalg.norm(_corpus_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # 0벡터 방지
    _corpus_embeddings = _corpus_embeddings / norms

    with open(idx_path, "r") as f:
        idx_map = json.load(f)
    _movie_ids = [idx_map[str(i)] for i in range(len(idx_map))]

    logger.info(
        "Loaded %d movie embeddings (%d dims, %.1f MB)",
        len(_movie_ids), _corpus_embeddings.shape[1],
        _corpus_embeddings.nbytes / 1024 / 1024
    )


def search_similar(query_embedding: np.ndarray, top_k: int = 100) -> list[tuple[int, float]]:
    """코사인 유사도 기반 Top-K 검색. (movie_id, score) 리스트 반환."""
    if _corpus_embeddings is None:
        return []

    query_norm = query_embedding / np.linalg.norm(query_embedding)
    scores = _corpus_embeddings @ query_norm  # (N,)

    # Top-K 추출 (argpartition은 O(N)으로 argsort O(N log N)보다 빠름)
    if top_k < len(scores):
        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
    else:
        top_indices = np.argsort(scores)[::-1][:top_k]

    return [(int(_movie_ids[i]), float(scores[i])) for i in top_indices]


def is_semantic_search_available() -> bool:
    """시맨틱 검색 사용 가능 여부"""
    return _corpus_embeddings is not None and len(_movie_ids) > 0
```

### 코드 예시 — Voyage AI 임베딩 클라이언트

```python
# backend/app/services/embedding.py

import logging
from functools import lru_cache

import httpx
import numpy as np

from app.core.config import settings
from app.services.llm import get_redis_client

logger = logging.getLogger(__name__)

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-multilingual-2"
EMBEDDING_DIM = 1024
CACHE_TTL = 86400  # 24시간


async def get_query_embedding(text: str) -> np.ndarray | None:
    """쿼리 텍스트를 Voyage AI로 임베딩 변환. Redis 캐싱 적용."""
    import hashlib

    cache_key = f"semantic_emb:{hashlib.md5(text.strip().lower().encode()).hexdigest()[:12]}"

    # Redis 캐시 확인
    redis = await get_redis_client()
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return np.frombuffer(cached, dtype=np.float32)
        except Exception:
            pass

    # Voyage AI API 호출
    api_key = settings.VOYAGE_API_KEY
    if not api_key:
        logger.error("VOYAGE_API_KEY not set")
        return None

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            VOYAGE_API_URL,
            json={
                "input": [text],
                "model": VOYAGE_MODEL,
                "input_type": "query",
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
        data = response.json()

    embedding = np.array(data["data"][0]["embedding"], dtype=np.float32)

    # Redis 캐시 저장
    if redis:
        try:
            await redis.setex(cache_key, CACHE_TTL, embedding.tobytes())
        except Exception:
            pass

    return embedding
```

---

## 6. 프론트엔드 변경

### 방안: 기존 SearchAutocomplete에 시맨틱 검색 통합

기존 키워드 검색과 **공존**하는 방식. 사용자 경험 변경 최소화.

### 변경 사항

#### 6-1. 검색 모드 자동 감지

```typescript
// lib/searchUtils.ts

/** 자연어 쿼리인지 판별 (간단 휴리스틱) */
export function isNaturalLanguageQuery(query: string): boolean {
  // 2단어 이하 → 키워드 검색 (영화 제목, 배우 이름)
  const words = query.trim().split(/\s+/);
  if (words.length <= 2) return false;

  // 자연어 패턴 감지
  const nlPatterns = [
    /좋은|어울리는|볼만한|추천/,     // 추천 요청
    /기분|분위기|느낌|감성/,         // 감성 표현
    /날씨|비|눈|맑은|흐린/,          // 날씨 관련
    /혼자|같이|연인|가족|친구/,       // 상황 표현
    /잔잔한|긴장감|무서운|재밌는|슬픈/, // 형용사
    /싶|때|날/,                      // 서술 패턴
  ];

  return nlPatterns.some(p => p.test(query));
}
```

#### 6-2. SearchAutocomplete 수정

```diff
 // components/search/SearchAutocomplete.tsx

+ import { isNaturalLanguageQuery } from "@/lib/searchUtils";
+ import { semanticSearch, type SemanticSearchResult } from "@/lib/api";

  // 자연어 감지 시 시맨틱 검색 결과도 표시
  useEffect(() => {
    const fetchResults = async () => {
+     // 자연어 쿼리 → 시맨틱 검색
+     if (isNaturalLanguageQuery(debouncedQuery)) {
+       setIsSemanticMode(true);
+       const semanticResults = await semanticSearch(debouncedQuery, 8);
+       setSemanticResults(semanticResults);
+     } else {
+       setIsSemanticMode(false);
+     }

      // 기존 키워드 검색 (항상 실행)
      const data = await searchAutocomplete(debouncedQuery);
      setResults(data);
    };
  }, [debouncedQuery]);
```

#### 6-3. 드롭다운에 시맨틱 결과 섹션 추가

```
┌──────────────────────────────────────────┐
│ 🔍  비오는 날 혼자 보기 좋은 잔잔한 영화    │ ← 입력
├──────────────────────────────────────────┤
│ ✨ AI 추천 결과                            │ ← 시맨틱 결과 (새로 추가)
│  🎬 쇼생크 탈출        ⭐ 9.1  드라마      │
│  🎬 인생은 아름다워     ⭐ 8.6  드라마      │
│  🎬 굿 윌 헌팅        ⭐ 8.3  드라마       │
│  🎬 어바웃 타임        ⭐ 7.9  로맨스      │
├──────────────────────────────────────────┤
│ 🎬 영화                                   │ ← 기존 키워드 결과
│  ...                                     │
├──────────────────────────────────────────┤
│ "비오는 날 혼자 보기 좋은..." 전체 검색     │
└──────────────────────────────────────────┘
```

#### 6-4. 전체 검색 결과 페이지 (`/movies`)

시맨틱 검색 결과를 전체 페이지에서도 표시. 기존 `/movies?query=` 로직에 분기 추가:

```typescript
// app/movies/page.tsx — 기존 검색과 공존

if (isNaturalLanguageQuery(query)) {
  // 시맨틱 검색 API 호출
  const semanticResults = await fetchSemanticSearch(query, limit, ageRating);
  // 결과를 기존 MovieCard 그리드로 렌더링
  // 상단에 "AI가 추천하는 결과" 배너 표시
} else {
  // 기존 키워드 검색 (현재 로직 그대로)
}
```

#### 6-5. API 함수 추가

```typescript
// lib/api.ts

export interface SemanticSearchResult {
  id: number;
  title: string;
  title_ko: string | null;
  poster_path: string | null;
  release_date: string | null;
  weighted_score: number | null;
  genres: string[];
  semantic_score: number;
  relevance_score: number;
  match_reason: string;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
  total: number;
  search_time_ms: number;
}

export async function semanticSearch(
  query: string,
  limit: number = 20,
  ageRating?: string
): Promise<SemanticSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (ageRating) params.set("age_rating", ageRating);
  return fetchAPI(`/movies/semantic-search?${params}`);
}
```

---

## 7. 임베딩 생성 스크립트 설계

### `backend/scripts/generate_embeddings.py`

```python
"""
42,917편 영화 임베딩 생성 스크립트.
Voyage AI voyage-multilingual-2 모델 사용.

사용법:
  cd backend
  python scripts/generate_embeddings.py [--batch-size 100] [--resume]

출력:
  data/embeddings/movie_embeddings.npy    (N, 1024) float32
  data/embeddings/movie_id_index.json     {"0": movie_id, ...}
  data/embeddings/embedding_metadata.json  메타 정보
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-multilingual-2"
EMBEDDING_DIM = 1024
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "embeddings"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"


def build_embedding_text(row: dict) -> str:
    """영화 1편의 임베딩용 텍스트 생성"""
    parts = []

    parts.append(f"제목: {row['title_ko'] or row['title']}")
    if row.get('title') and row['title'] != row.get('title_ko'):
        parts.append(f"영어 제목: {row['title']}")

    if row.get('genres'):
        parts.append(f"장르: {row['genres']}")

    if row.get('overview'):
        parts.append(f"줄거리: {row['overview'][:500]}")

    # emotion_tags → 자연어 변환
    if row.get('emotion_tags'):
        emotion_labels = {
            'healing': '힐링/치유', 'tension': '긴장/스릴',
            'energy': '활기/에너지', 'romance': '로맨스/감성',
            'deep': '깊은/철학적', 'fantasy': '판타지/상상',
            'light': '가벼운/유쾌'
        }
        tags = row['emotion_tags'] if isinstance(row['emotion_tags'], dict) else json.loads(row['emotion_tags'])
        high = [emotion_labels[k] for k, v in tags.items() if isinstance(v, (int, float)) and v >= 0.5]
        if high:
            parts.append(f"분위기: {', '.join(high)}")

    # weather_scores → 자연어
    if row.get('weather_scores'):
        weather_labels = {'sunny': '맑은 날', 'rainy': '비 오는 날', 'cloudy': '흐린 날', 'snowy': '눈 오는 날'}
        ws = row['weather_scores'] if isinstance(row['weather_scores'], dict) else json.loads(row['weather_scores'])
        high_w = [weather_labels[k] for k, v in ws.items() if isinstance(v, (int, float)) and v >= 0.3]
        if high_w:
            parts.append(f"어울리는 날씨: {', '.join(high_w)}")

    if row.get('keywords'):
        parts.append(f"키워드: {row['keywords']}")

    if row.get('director_ko'):
        parts.append(f"감독: {row['director_ko']}")

    return '\n'.join(parts)


def embed_batch(texts: list[str], api_key: str) -> list[list[float]]:
    """Voyage AI API로 배치 임베딩 (최대 128개)"""
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            VOYAGE_API_URL,
            json={"input": texts, "model": VOYAGE_MODEL, "input_type": "document"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
    return [item["embedding"] for item in data["data"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--resume", action="store_true", help="이전 진행 이어서")
    args = parser.parse_args()

    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        logger.error("VOYAGE_API_KEY 환경변수 필요")
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL", "postgresql://recflix:recflix123@localhost:5432/recflix")
    engine = create_engine(db_url)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 영화 데이터 로드
    with Session(engine) as session:
        rows = session.execute(text("""
            SELECT m.id, m.title, m.title_ko, m.overview, m.director_ko,
                   m.emotion_tags::text, m.weather_scores::text, m.mbti_scores::text,
                   (SELECT string_agg(g.name, ', ') FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE mg.movie_id = m.id) as genres,
                   (SELECT string_agg(k.name, ', ') FROM movie_keywords mk JOIN keywords k ON k.id = mk.keyword_id WHERE mk.movie_id = m.id) as keywords
            FROM movies m
            ORDER BY m.id
        """)).fetchall()

    columns = ['id', 'title', 'title_ko', 'overview', 'director_ko',
               'emotion_tags', 'weather_scores', 'mbti_scores', 'genres', 'keywords']
    movies = [dict(zip(columns, row)) for row in rows]

    # JSONB 문자열 파싱
    for m in movies:
        for field in ['emotion_tags', 'weather_scores', 'mbti_scores']:
            if m[field] and isinstance(m[field], str):
                m[field] = json.loads(m[field])

    logger.info("총 %d편 영화 로드", len(movies))

    # 진행 상태 로드 (resume 모드)
    start_idx = 0
    all_embeddings = []
    if args.resume and PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
        start_idx = progress.get("completed", 0)
        partial_path = OUTPUT_DIR / "movie_embeddings_partial.npy"
        if partial_path.exists():
            all_embeddings = np.load(str(partial_path)).tolist()
        logger.info("이전 진행에서 재개: %d/%d", start_idx, len(movies))

    # 배치 임베딩 생성
    total = len(movies)
    batch_size = args.batch_size
    t_start = time.time()

    for i in range(start_idx, total, batch_size):
        batch = movies[i:i + batch_size]
        texts = [build_embedding_text(m) for m in batch]

        try:
            embeddings = embed_batch(texts, api_key)
            all_embeddings.extend(embeddings)
        except Exception as e:
            logger.error("배치 %d 실패: %s", i, e)
            # 진행 저장 후 종료
            _save_progress(i, all_embeddings, movies)
            sys.exit(1)

        elapsed = time.time() - t_start
        done = i + len(batch)
        eta = (elapsed / done) * (total - done) if done > 0 else 0
        logger.info(
            "[%d/%d] %.1f%% | %.0fs elapsed | ETA %.0fs",
            done, total, done / total * 100, elapsed, eta
        )

        # 1000개마다 중간 저장
        if done % 1000 == 0:
            _save_progress(done, all_embeddings, movies)

        # Rate limit (Voyage AI: 300 RPM)
        time.sleep(0.25)

    # 최종 저장
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    np.save(str(OUTPUT_DIR / "movie_embeddings.npy"), embeddings_array)

    movie_id_index = {str(i): movies[i]["id"] for i in range(len(movies))}
    with open(OUTPUT_DIR / "movie_id_index.json", "w") as f:
        json.dump(movie_id_index, f)

    metadata = {
        "model": VOYAGE_MODEL,
        "dims": EMBEDDING_DIM,
        "count": len(movies),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_size_mb": round(embeddings_array.nbytes / 1024 / 1024, 1),
    }
    with open(OUTPUT_DIR / "embedding_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # 정리
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    partial_path = OUTPUT_DIR / "movie_embeddings_partial.npy"
    if partial_path.exists():
        partial_path.unlink()

    logger.info("완료! %d편, %d차원, %.1f MB", *embeddings_array.shape, embeddings_array.nbytes / 1024 / 1024)


def _save_progress(completed: int, embeddings: list, movies: list):
    """중간 진행 저장"""
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"completed": completed}, f)
    if embeddings:
        partial = np.array(embeddings, dtype=np.float32)
        np.save(str(OUTPUT_DIR / "movie_embeddings_partial.npy"), partial)
    logger.info("진행 저장: %d/%d", completed, len(movies))


if __name__ == "__main__":
    main()
```

### 스크립트 실행

```bash
cd backend

# 1. 환경변수 설정
export VOYAGE_API_KEY="your-voyage-api-key"

# 2. 전체 실행 (~7분, 100개씩 배치, 0.25초 딜레이)
python scripts/generate_embeddings.py --batch-size 100

# 3. 중단 후 재개
python scripts/generate_embeddings.py --batch-size 100 --resume
```

### 예상 시간/비용

| 항목 | 값 |
|------|-----|
| 총 영화 수 | 42,917편 |
| 배치 크기 | 100편 |
| 배치 수 | ~430개 |
| API 호출 간격 | 0.25초 |
| 예상 총 시간 | **~7분** (API 호출 + 딜레이) |
| 예상 토큰 | ~3M (50M 무료 한도 이내) |
| 비용 | **$0** |
| 출력 파일 크기 | ~176MB (.npy) |

---

## 8. 예상 리소스

### DB 용량 변화

| 항목 | 현재 | 추가 |
|------|------|------|
| Railway PostgreSQL | 145 MB | 0 MB (DB에 벡터 미저장) |
| .npy 파일 (Railway 볼륨 or 배포 시 포함) | - | ~176 MB |
| movie_id_index.json | - | ~0.5 MB |

### 서버 메모리 변화

| 항목 | 현재 | 추가 | 합계 |
|------|------|------|------|
| FastAPI + SQLAlchemy + Redis | ~200-300 MB | - | - |
| 임베딩 행렬 (42,917 × 1,024 × 4B) | - | ~176 MB | - |
| **총 예상** | ~300 MB | ~176 MB | **~476 MB** |

Railway Hobby 플랜 8GB RAM 기준 충분. 단, .npy 파일은 Railway 볼륨 또는 배포 아티팩트에 포함 필요.

### 검색 응답 시간 예상

| 단계 | 시간 |
|------|------|
| Redis 캐시 히트 시 | ~1-5ms |
| Voyage API 쿼리 임베딩 | ~100-200ms |
| NumPy 코사인 유사도 (42K × 1024) | ~10-20ms |
| DB 후보 조회 (100편) | ~20-50ms |
| 하이브리드 재랭킹 | ~5-10ms |
| **총 (캐시 미스)** | **~150-300ms** |
| **총 (임베딩 캐시 히트)** | **~40-80ms** |

---

## 9. 구현 계획 (Phase 33)

### 단계별 실행 순서

| 순서 | 작업 | 예상 시간 |
|------|------|----------|
| 1 | Voyage AI 계정 생성 + API 키 발급 | 5분 |
| 2 | `backend/app/services/embedding.py` 작성 (Voyage AI 클라이언트) | 20분 |
| 3 | `backend/scripts/generate_embeddings.py` 작성 + 로컬 실행 | 30분 |
| 4 | `backend/app/api/v1/semantic_search.py` 작성 (벡터 검색 모듈) | 40분 |
| 5 | `backend/app/main.py` — lifespan에 임베딩 로드 추가 | 10분 |
| 6 | movies.py에 `/movies/semantic-search` 엔드포인트 추가 | 30분 |
| 7 | `frontend/lib/api.ts` — semanticSearch API 함수 추가 | 10분 |
| 8 | `frontend/lib/searchUtils.ts` — 자연어 감지 유틸 | 10분 |
| 9 | SearchAutocomplete 시맨틱 결과 섹션 추가 | 40분 |
| 10 | 영화 검색 페이지 시맨틱 모드 분기 | 30분 |
| 11 | config.py에 `VOYAGE_API_KEY` 추가 | 5분 |
| 12 | requirements.txt 업데이트 (voyageai 또는 httpx만 사용) | 5분 |
| 13 | 프로덕션 배포 (Railway에 .npy 포함 + Vercel) | 20분 |

### 새로 추가/변경되는 파일

```
새로 생성:
  backend/app/services/embedding.py          # Voyage AI 클라이언트
  backend/app/api/v1/semantic_search.py      # 벡터 검색 모듈
  backend/scripts/generate_embeddings.py     # 임베딩 생성 스크립트
  backend/data/embeddings/                   # 벡터 데이터 디렉토리
  frontend/lib/searchUtils.ts                # 자연어 감지 유틸

수정:
  backend/app/core/config.py                 # VOYAGE_API_KEY 추가
  backend/app/api/v1/movies.py               # 시맨틱 검색 엔드포인트 추가
  backend/app/api/v1/router.py               # semantic_search 라우터 등록
  backend/app/main.py                        # lifespan에 임베딩 로드
  backend/requirements.txt                   # (httpx는 이미 있으므로 변경 불필요)
  frontend/lib/api.ts                        # semanticSearch 함수 추가
  frontend/components/search/SearchAutocomplete.tsx  # 시맨틱 결과 섹션
  frontend/app/movies/page.tsx               # 시맨틱 검색 모드 분기
```

### 환경변수 추가

```bash
# backend/.env (로컬)
VOYAGE_API_KEY=your-voyage-api-key

# Railway (프로덕션)
VOYAGE_API_KEY=your-voyage-api-key
```

---

## 10. 리스크 및 대안

| 리스크 | 영향 | 대안 |
|--------|------|------|
| Voyage AI 무료 한도 소진 | 쿼리 임베딩 불가 | Redis 캐시로 동일 쿼리 재사용 최소화 / OpenAI로 폴백 |
| Railway에서 176MB .npy 로드 시간 | 서버 시작 느려짐 (~5초) | lazy loading 또는 mmap 모드 (`np.load(mmap_mode='r')`) |
| 한국어 검색 품질 부족 | 관련 없는 결과 반환 | 임베딩 텍스트 템플릿 튜닝 / 쿼리 전처리 추가 |
| Voyage AI 서비스 장애 | 시맨틱 검색 불가 | 기존 키워드 검색으로 graceful fallback |

### Graceful Degradation

```python
# 시맨틱 검색 불가 시 기존 검색으로 폴백
@router.get("/semantic-search")
async def semantic_search(q: str, ...):
    if not is_semantic_search_available():
        # 기존 키워드 검색으로 리다이렉트
        return await keyword_search_fallback(q, limit, age_rating, db)

    embedding = await get_query_embedding(q)
    if embedding is None:
        # 임베딩 실패 시에도 키워드 폴백
        return await keyword_search_fallback(q, limit, age_rating, db)

    # 정상 시맨틱 검색 진행
    ...
```
