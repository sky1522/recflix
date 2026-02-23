claude "Phase 38: 프로덕션 DB 마이그레이션 — Phase 29-32 스키마 적용 + 소셜 로그인 E2E 검증.

=== Research ===
먼저 다음 파일들을 읽고 현재 상태를 파악할 것:
- CLAUDE.md
- backend/scripts/migrate_phase4.sql (마이그레이션 SQL 전체 내용)
- backend/app/models/user.py (users 모델 — 6컬럼 추가 여부)
- backend/app/models/user_event.py (user_events 모델)
- backend/app/api/v1/auth.py (소셜 로그인 로직 — Kakao/Google OAuth)
- backend/app/api/v1/events.py (이벤트 API)
- backend/app/core/config.py (OAuth 환경변수 — KAKAO_*, GOOGLE_*)
- frontend/app/auth/kakao/callback/page.tsx (프론트 콜백)
- frontend/app/auth/google/callback/page.tsx (프론트 콜백)

=== 1단계: 마이그레이션 SQL 검증 ===
migrate_phase4.sql 내용을 읽고 다음을 확인:
1. user_events 테이블 CREATE 문이 user_event.py 모델과 일치하는지
2. users ALTER TABLE 6컬럼이 user.py 모델과 일치하는지
   - experiment_group, kakao_id, google_id, profile_image, onboarding_completed, preferred_genres
3. 필요한 인덱스가 포함되어 있는지 (kakao_id UNIQUE, google_id UNIQUE 등)
4. IF NOT EXISTS / ADD COLUMN IF NOT EXISTS로 멱등성 보장되는지

누락/불일치가 있으면 migrate_phase4.sql을 수정하여 모델과 완전히 일치시킬 것.

=== 2단계: 프로덕션 DB 마이그레이션 실행 ===
Railway PostgreSQL에 직접 SQL 실행:

PGPASSWORD=lWpLnODyZTJaAUvChkycxupwZPlMOtad psql -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway -f backend/scripts/migrate_phase4.sql

실행 후 검증:
- \d user_events → 테이블 존재 + 컬럼 확인
- \d users → 6개 새 컬럼 존재 확인
- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;

=== 3단계: Railway 환경변수 확인 ===
Railway Dashboard에서 Backend 서비스의 환경변수 확인 (직접 접근 불가하므로 코드 기준 체크):
- config.py에서 KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET, KAKAO_REDIRECT_URI 확인
- config.py에서 GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI 확인
- frontend .env / Vercel 환경변수: NEXT_PUBLIC_KAKAO_*, NEXT_PUBLIC_GOOGLE_* 확인

체크리스트를 출력할 것 (수동 확인용):
┌──────────────────────────┬──────────┬─────────────────────┐
│ 환경변수                  │ 위치     │ 설정 필요 값 (예시)  │
├──────────────────────────┼──────────┼─────────────────────┤
│ KAKAO_CLIENT_ID          │ Railway  │ Kakao Developer 앱키│
│ ...                      │ ...      │ ...                 │
└──────────────────────────┴──────────┴─────────────────────┘

=== 4단계: 헬스체크 검증 ===
프로덕션 Backend 재배포 후:
curl https://backend-production-cff2.up.railway.app/api/v1/health
→ DB 연결 OK, 새 테이블 접근 가능 확인

=== 5단계: API 엔드포인트 스모크 테스트 ===
마이그레이션 후 기존 기능 깨지지 않았는지 확인:
1. curl 'https://backend-production-cff2.up.railway.app/api/v1/movies?page_size=1' → 200
2. curl 'https://backend-production-cff2.up.railway.app/api/v1/recommendations?weather=sunny&limit=3' → 200 + recommendation_reason 포함
3. curl 'https://backend-production-cff2.up.railway.app/api/v1/movies/search/semantic?q=따뜻한+가족+영화&limit=3' → 200

=== 규칙 ===
- 기존 테이블 DROP/TRUNCATE 절대 금지
- ALTER TABLE은 IF NOT EXISTS로 멱등성 보장
- 마이그레이션 전 현재 users 행 수 확인 (데이터 유실 방지)
- .md 문서 파일 건드리지 말 것

=== 검증 ===
1. 프로덕션 DB에 user_events 테이블 존재
2. 프로덕션 DB users 테이블에 6개 신규 컬럼 존재
3. 헬스체크 200 OK
4. 기존 API 3개 스모크 테스트 통과
5. 환경변수 체크리스트 출력 완료
6. git add -A && git commit -m 'ops: Phase 38 프로덕션 DB 마이그레이션 (user_events + users 6컬럼)' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 마이그레이션 실행 결과 (성공/실패)
- 테이블 구조 검증 결과
- 환경변수 체크리스트
- 스모크 테스트 결과
- 프로덕션 소셜 로그인 활성화까지 남은 수동 작업 목록"