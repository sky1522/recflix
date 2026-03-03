# 트레일러 UX 변경 + 홈 한국 인기 영화 섹션 구현 결과

> 작업일: 2026-03-03

## 변경 파일 목록
| 파일 | 변경 내용 |
|------|-----------|
| `frontend/app/movies/[id]/components/MovieHero.tsx` | trailerKey prop 추가, 시청하기 버튼 → YouTube 새 탭 열기, ExternalLink 아이콘, trailer_key 없으면 버튼 숨김 |
| `frontend/app/movies/[id]/page.tsx` | MovieTrailer import/사용 제거, MovieHero에 trailerKey prop 전달 |
| `frontend/app/page.tsx` | getMovies import 추가, 한국 인기 영화 별도 fetch, MovieRow로 렌더링 |

## 기능 1: 트레일러 UX 변경

### 변경 사항
- **인라인 YouTube iframe 제거**: `MovieTrailer` 컴포넌트 사용을 `page.tsx`에서 완전히 제거 (컴포넌트 파일은 유지)
- **시청하기 버튼 수정** (`MovieHero.tsx`):
  - `trailerKey` prop 추가
  - 클릭 시 `window.open('https://www.youtube.com/watch?v=${trailerKey}', '_blank')` 실행
  - `ExternalLink` 아이콘 추가로 외부 링크 표시
  - `trailer_key` 없는 영화 → 버튼 자체를 숨김 (조건부 렌더링)

### 프로덕션 검증
- `youtube.com/watch` (새 탭 링크): JS 번들에 포함 확인
- `youtube.com/embed` (인라인 iframe): JS 번들에서 제거 확인

## 기능 2: 홈 한국 인기 영화 섹션

### 변경 사항
- **별도 API 호출**: `getMovies({ country: "대한민국", sort_by: "popularity", page_size: 20 })` — recommendations API와 독립
- **MovieRow 재사용**: `title="한국 인기 영화"`, `subtitle="지금 한국에서 사랑받는 영화들"`, `section="korean_popular"`
- **위치**: 추천 섹션들(인기, 평점, MBTI, 날씨, 기분) 아래에 배치
- **비로그인 사용자에게도 표시**

### 프로덕션 검증
- 백엔드 API: `country=대한민국&sort_by=popularity` → 1,097편 반환 (대홍수, 전지적 독자 시점 등)
- 프론트엔드 번들: `korean_popular`, `대한민국` 문자열 포함 확인

## 완료 조건 체크

### 트레일러
- [x] 영화 상세 페이지에서 인라인 YouTube iframe 제거됨
- [x] "시청하기" 버튼 클릭 → YouTube 새 탭 열림
- [x] trailer_key 없는 영화 → 버튼 숨김
- [x] 모바일에서도 새 탭 정상 열림 (window.open + _blank)

### 한국 인기 영화
- [x] 홈 페이지에 "한국 인기 영화" 섹션 표시됨
- [x] 한국 제작 영화가 인기순으로 정렬되어 표시
- [x] MovieRow 가로 스크롤 정상 동작
- [x] 비로그인 사용자에게도 표시

## 배포
- 커밋: `325df0c` (`feat: 트레일러 새 탭 열기 + 홈 한국 인기 영화 섹션`)
- Vercel 프로덕션: https://jnsquery-reflix.vercel.app (수동 배포 완료)
- GitHub Secrets: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, RAILWAY_TOKEN 모두 등록됨 → CI/CD 자동 배포 활성화
