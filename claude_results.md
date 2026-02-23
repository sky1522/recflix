# Phase 45: 코드 품질 자동화 + Phase 44 잔여 수정 (2026-02-23)

## Step 0: Phase 44 잔여 수정

### 0-1: layout.tsx fallback description
- 확인 결과 이미 정상: `${title} - RecFlix에서 확인하세요`
- 수정 불필요

### 0-2: MovieModal focus trap
- Tab/Shift+Tab 순환 로직 추가 (순수 JS, querySelectorAll)
- 열릴 때: trigger 요소 저장 + dialog에 focus
- Tab: 마지막 → 첫 번째 순환
- Shift+Tab: 첫 번째 → 마지막 순환
- 닫힐 때: trigger 요소로 포커스 복귀

### 0-3: HeaderMobileDrawer focus trap
- 동일한 Tab 순환 로직
- panelRef + tabIndex={-1} + outline-none
- 열릴 때 패널에 focus, 닫힐 때 trigger 복귀

### 0-4: SearchResults option tabIndex={-1}
- 4개 option 버튼 모두 `tabIndex={-1}` 추가
- combobox에서 Tab이 입력 필드 밖으로 나가지 않도록 방지

## Step 1: Backend ruff 자동수정

| 단계 | 명령 | 수정 건수 |
|------|------|----------|
| Safe auto-fix | `ruff check app/ --fix` | 59건 |
| UP007 unsafe | `ruff check app/ --fix --unsafe-fixes --select UP007` | 76건 |
| F401 cleanup | `ruff check app/ --fix --select F401` | 14건 (미사용 Optional 임포트) |
| I001 sort | `ruff check app/ --fix --select I001` | 1건 |
| **합계** | | **150건 자동수정** |

## Step 2: Backend 수동 수정

### 2-1: E402 (main.py 3건) — noqa 주석
- `from app.api.v1.router import api_router  # noqa: E402`
- `from app.database import Base, engine  # noqa: E402`
- `from app.models import *  # noqa: E402, F401, F403`

### 2-2: B904 (deps.py 1건) — 예외 체인
- `raise credentials_exception` → `raise credentials_exception from e`

### 2-3: SIM105 (3건) — contextlib.suppress
- `movies.py:100`: Redis cache setex → `contextlib.suppress(RedisError, ConnectionError, TimeoutError)`
- `movies.py:451`: Redis cache setex → 동일
- `security.py:133`: Redis delete → 동일

### 2-4: SIM108 (1건) — ternary
- `weather.py:412`: if-else → `condition = "sunny" if 6 <= hour < 18 else "cloudy"`

### 2-5: Broad except 구체화 (32건 → 0건)

| 파일 | 변경 수 | 예외 타입 |
|------|---------|----------|
| `core/security.py` | 3 | `(RedisError, ConnectionError, TimeoutError)` |
| `services/embedding.py` | 5 | Redis + `(httpx.HTTPError, TimeoutError)` |
| `services/llm.py` | 5 | Redis + `(anthropic.APIError, ...)` |
| `services/weather.py` | 8+ | Redis + httpx + `(ValueError, KeyError, TypeError)` |
| `api/v1/events.py` | 2 | `SQLAlchemyError` |
| `api/v1/health.py` | 2 | `SQLAlchemyError` / `(RedisError, ConnectionError)` |
| `api/v1/movies.py` | 4 | `(RedisError, ConnectionError, TimeoutError)` |
| `api/v1/recommendation_cf.py` | 1 | `(FileNotFoundError, OSError, ValueError)` |
| `api/v1/semantic_search.py` | 1 | `(OSError, ValueError)` |

## Step 3: Frontend any 감축

### Before/After
- `catch (err: any)`: 2건 → 0건 (`err: unknown` + `instanceof Error`)
- `as any` (genre): 6건 → 0건 (`GenreLike` 타입 + `getGenreName()` 유틸)

### 새로 추가된 타입/유틸
- `types/index.ts`: `GenreLike = string | { id?: number; name?: string; name_ko?: string }`
- `lib/utils.ts`: `getGenreName(genre: GenreLike): string`

### 수정 파일 (8건)
1. `login/page.tsx` — `catch (err: unknown)`
2. `signup/page.tsx` — `catch (err: unknown)`
3. `FeaturedBanner.tsx` — `getGenreName(genre)`
4. `HybridMovieCard.tsx` — `getGenreName(movie.genres[0])`
5. `MovieCard.tsx` — `getGenreName(movie.genres[0])`
6. `MovieModal.tsx` — `getGenreName(genre)`
7. `ratings/page.tsx` — `getGenreName(g)`
8. `MovieHero.tsx` — `getGenreName(genre)`

## 검증 결과

| 항목 | 결과 |
|------|------|
| `ruff check app/` | 0 issues (143 → 0) |
| `python -c 'from app.main import app; print(app.title)'` | `RecFlix` (정상) |
| `tsc --noEmit` | 0 errors |
| `npm run build` | 성공 (13/13 pages) |
| `npm run lint` | 0 warnings/errors |
| `grep ': any' frontend/app/ frontend/components/` | 0건 |
| `grep 'as any' frontend/app/ frontend/components/` | 0건 |

## 변경 파일 목록

### Frontend (12개)
- `types/index.ts` — GenreLike 타입 추가
- `lib/utils.ts` — getGenreName 유틸 추가
- `components/movie/MovieModal.tsx` — focus trap + getGenreName
- `components/movie/FeaturedBanner.tsx` — getGenreName
- `components/movie/HybridMovieCard.tsx` — getGenreName
- `components/movie/MovieCard.tsx` — getGenreName
- `components/layout/HeaderMobileDrawer.tsx` — focus trap
- `components/search/SearchResults.tsx` — tabIndex={-1}
- `app/login/page.tsx` — err: unknown
- `app/signup/page.tsx` — err: unknown
- `app/ratings/page.tsx` — getGenreName
- `app/movies/[id]/components/MovieHero.tsx` — getGenreName

### Backend (13개)
- `main.py` — noqa E402
- `core/deps.py` — raise from e
- `core/security.py` — contextlib.suppress + RedisError
- `services/embedding.py` — except 구체화
- `services/llm.py` — except 구체화
- `services/weather.py` — except 구체화 + ternary
- `api/v1/events.py` — SQLAlchemyError
- `api/v1/health.py` — SQLAlchemyError + RedisError
- `api/v1/movies.py` — contextlib.suppress + RedisError
- `api/v1/recommendation_cf.py` — FileNotFoundError 등
- `api/v1/semantic_search.py` — OSError 등
- `api/v1/interactions.py` — ruff auto-fix
- `schemas/*.py`, `config.py` — Optional→X|None, import 정리
