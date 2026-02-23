# Phase 38: 프로덕션 DB 마이그레이션 — 결과

## 날짜
2026-02-23

## 마이그레이션 실행 결과

**상태: 성공 (멱등 실행)**

프로덕션 Railway DB에 테이블과 컬럼이 이미 존재했음 (SQLAlchemy `create_all`로 사전 생성).
`IF NOT EXISTS`로 안전하게 스킵되고, 타입/제약조건 보정만 실행됨.

### 실행된 보정 작업

| 작업 | 변경 전 | 변경 후 |
|------|---------|---------|
| `preferred_genres` 타입 수정 | `text[]` (ARRAY) | `text` (TEXT) |
| `auth_provider` 제약조건 | nullable=YES | NOT NULL DEFAULT 'email' |
| `onboarding_completed` 제약조건 | nullable=YES | NOT NULL DEFAULT false |
| A/B 그룹 재배정 | control 5명 | 3등분 배정 |

### 데이터 무결성

| 항목 | 마이그레이션 전 | 마이그레이션 후 |
|------|---------------|---------------|
| users 행 수 | 8 | 8 (변동 없음) |
| user_events 테이블 | 존재 | 존재 (변동 없음) |

## 테이블 구조 검증 결과

### users 테이블 (17컬럼) — 모델과 일치 확인

| 컬럼 | 타입 | Nullable | Default | 모델 일치 |
|------|------|----------|---------|----------|
| id | integer | NO | serial | OK |
| email | varchar | NO | - | OK |
| password | varchar | NO | - | OK |
| nickname | varchar | NO | - | OK |
| mbti | varchar | YES | - | OK |
| birth_date | date | YES | - | OK |
| location_consent | boolean | YES | - | OK |
| is_active | boolean | YES | - | OK |
| created_at | timestamp | YES | - | OK |
| updated_at | timestamp | YES | - | OK |
| **experiment_group** | varchar | NO | 'control' | OK |
| **kakao_id** | varchar | YES | - | OK (UNIQUE) |
| **google_id** | varchar | YES | - | OK (UNIQUE) |
| **profile_image** | varchar | YES | - | OK |
| **auth_provider** | varchar | **NO** | 'email' | OK (수정됨) |
| **onboarding_completed** | boolean | **NO** | false | OK (수정됨) |
| **preferred_genres** | **text** | YES | - | OK (수정됨) |

### user_events 테이블 (7컬럼) — 모델과 일치 확인

| 컬럼 | 타입 | Nullable | 모델 일치 |
|------|------|----------|----------|
| id | integer (serial) | NO | OK |
| user_id | integer (FK users.id) | YES | OK |
| session_id | varchar | YES | OK |
| event_type | varchar | NO | OK |
| movie_id | integer | YES | OK |
| metadata | jsonb | YES | OK |
| created_at | timestamptz | YES | OK |

### 인덱스 확인

**users**: `users_pkey`, `ix_users_email` (UNIQUE), `users_kakao_id_key` (UNIQUE), `users_google_id_key` (UNIQUE), `ix_users_kakao_id` (partial), `ix_users_google_id` (partial)

**user_events**: `user_events_pkey`, `ix_user_events_event_type`, `ix_user_events_created_at`, `idx_events_user_time`, `idx_events_type_time`, `idx_events_movie`

## 코드 버그 수정

### events.py ab-report 쿼리 컬럼명 버그 수정

| 파일 | 변경 | 이유 |
|------|------|------|
| `backend/app/api/v1/events.py` | raw SQL `metadata_` → `metadata` (4곳) | DB 컬럼명은 `metadata`, Python 속성은 `metadata_` — raw SQL에서는 DB 컬럼명 사용 필요 |

## 환경변수 체크리스트

### Backend (Railway 환경변수)

| 환경변수 | 용도 | 설정 필요 값 |
|---------|------|-------------|
| `KAKAO_CLIENT_ID` | 카카오 OAuth | Kakao Developer 앱 REST API 키 |
| `KAKAO_CLIENT_SECRET` | 카카오 OAuth | Kakao Developer 앱 시크릿 |
| `KAKAO_REDIRECT_URI` | 카카오 콜백 | `https://jnsquery-reflix.vercel.app/auth/kakao/callback` |
| `GOOGLE_CLIENT_ID` | Google OAuth | Google Cloud Console 클라이언트 ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth | Google Cloud Console 시크릿 |
| `GOOGLE_REDIRECT_URI` | Google 콜백 | `https://jnsquery-reflix.vercel.app/auth/google/callback` |

### Frontend (Vercel 환경변수)

| 환경변수 | 용도 | 설정 필요 값 |
|---------|------|-------------|
| `NEXT_PUBLIC_KAKAO_CLIENT_ID` | 카카오 OAuth 리다이렉트 | Kakao Developer 앱 REST API 키 |
| `NEXT_PUBLIC_KAKAO_REDIRECT_URI` | 카카오 콜백 URL | `https://jnsquery-reflix.vercel.app/auth/kakao/callback` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth 리다이렉트 | Google Cloud Console 클라이언트 ID |
| `NEXT_PUBLIC_GOOGLE_REDIRECT_URI` | Google 콜백 URL | `https://jnsquery-reflix.vercel.app/auth/google/callback` |

> 로컬 `.env.local`에는 이미 설정됨 (localhost 콜백). Vercel에도 프로덕션 값이 설정되어 있어야 함.

## 스모크 테스트 결과

| API | 상태 | 비고 |
|-----|------|------|
| `GET /health` | 200 `{"status": "healthy"}` | DB/Redis/SVD/임베딩 정상 |
| `GET /api/v1/movies?page_size=1` | 200 | 영화 데이터 정상 반환 |
| `GET /api/v1/recommendations?weather=sunny&limit=3` | 200 | 추천 + recommendation_reason 포함 |
| `GET /api/v1/movies/semantic-search?q=따뜻한+가족+영화&limit=3` | 200 | 시맨틱 검색 정상 |

## 변경 파일

| 파일 | 작업 |
|------|------|
| `backend/scripts/migrate_phase4.sql` | user_events CREATE TABLE 추가 + 타입/제약조건 보정 추가 |
| `backend/app/api/v1/events.py` | raw SQL `metadata_` → `metadata` 버그 수정 (4곳) |

## 프로덕션 소셜 로그인 활성화까지 남은 수동 작업

1. **Railway 환경변수 확인**: 위 6개 OAuth 환경변수가 프로덕션 값으로 설정되어 있는지 확인
2. **Vercel 환경변수 확인**: 위 4개 `NEXT_PUBLIC_*` 환경변수가 프로덕션 콜백 URL로 설정되어 있는지 확인
3. **Kakao Developer Console**: 앱 도메인에 `jnsquery-reflix.vercel.app` 등록 + Redirect URI 설정
4. **Google Cloud Console**: 승인된 리디렉션 URI에 `https://jnsquery-reflix.vercel.app/auth/google/callback` 추가
5. **CI/CD 자동 배포**: 코드 변경 push 시 GitHub Actions가 Railway CD 실행 (events.py 버그 수정 반영)
