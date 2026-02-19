# 소셜 로그인 키 불일치 수정 결과

## 날짜
2026-02-19

## 1단계: 환경변수 대조 결과
| 위치 | KAKAO_CLIENT_ID | KAKAO_CLIENT_SECRET | 일치 |
|------|----------------|--------------------|----|
| Frontend .env.local | (없었음 → 새로 생성) | - | - |
| Backend .env | (OAuth 키 없음, Railway만 사용) | (없음) | - |
| Vercel | f5ba90d44f47ba930e20cde00843cc80 | - | ✅ |
| Railway | f5ba90d44f47ba930e20cde00843cc80 | xKK3FaZSCRXlAMD9Zby4D92TxPdV0jsG | ✅ |

| 위치 | GOOGLE_CLIENT_ID | GOOGLE_CLIENT_SECRET | 일치 |
|------|----------------|--------------------|----|
| Vercel | 222719323914-...googleusercontent.com | - | ✅ |
| Railway | 222719323914-...googleusercontent.com | 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 | ✅ |

## 2단계: 키 통일 필요 여부
Frontend(Vercel)와 Backend(Railway)의 키 값은 일치. 키 통일 불필요.

## 근본 원인: Vercel 환경변수 값에 줄바꿈 문자(\n) 포함!
Hex dump 분석 결과, Vercel에 등록된 NEXT_PUBLIC_* 환경변수 4개 모두 값 끝에 `\n`(0x5c6e) 문자가 포함되어 있었음.
→ URLSearchParams가 `\n`을 `%0A`로 인코딩 → OAuth 제공자가 값 불일치로 거부 → 400 에러

## 3단계: URL 생성 로직 수정
| 파일 | 변경 |
|------|------|
| frontend/app/login/page.tsx | 카카오+Google 버튼: URLSearchParams + `.trim()` 적용 |
| frontend/app/signup/page.tsx | 카카오+Google 버튼: URLSearchParams + `.trim()` 적용 |
| frontend/app/auth/google/callback/page.tsx | 에러 상세 정보 전달 (detail 파라미터) |
| frontend/app/auth/kakao/callback/page.tsx | 에러 상세 정보 전달 (detail 파라미터) |
| frontend/app/login/page.tsx | OAuth 에러 메시지 표시 (useSearchParams) |

## 4단계: Backend 토큰 교환 검증
- client_id 일치: ✅ (Frontend Vercel == Backend Railway)
- client_secret 짝 맞음: ✅ (f5ba → xKK3, Google → GOCSPX)
- redirect_uri 일치: ✅ (모두 jnsquery-reflix.vercel.app/auth/*/callback)

## 5단계: .env.local 숨겨진 문자
**발견!** Vercel 환경변수 4개 모두 값 끝에 `\n` 포함.
- NEXT_PUBLIC_KAKAO_CLIENT_ID: `f5ba...cc80\n` → `f5ba...cc80`
- NEXT_PUBLIC_KAKAO_REDIRECT_URI: `...callback\n` → `...callback`
- NEXT_PUBLIC_GOOGLE_CLIENT_ID: `222719...com\n` → `222719...com`
- NEXT_PUBLIC_GOOGLE_REDIRECT_URI: `...callback\n` → `...callback`

## 수정 조치
1. Vercel 환경변수 4개 삭제 후 `printf`(줄바꿈 없이)로 재등록
2. frontend/.env.local 새로 생성 (깨끗한 값)
3. 코드에 `.trim()` 추가 (이중 안전장치)
4. 카카오 버튼도 URLSearchParams로 교체
5. 콜백 페이지 에러 상세 표시 추가
6. 로그인 페이지 OAuth 에러 메시지 표시 추가

## 검증 결과
- Hex dump 확인: 프로덕션 번들에서 `\n` 제거됨 ✅
- 카카오 Client ID: `f5ba90d44f47ba930e20cde00843cc80` (깨끗) ✅
- Google Client ID: `222719323914-...googleusercontent.com` (깨끗) ✅
- `.trim()` 코드 적용 확인 ✅
