# 기능 구현 2건: 트레일러 UX 변경 + 메인 한국 인기 영화 섹션

## 기능 1: 트레일러 인라인 iframe 제거 → 시청하기 버튼으로 YouTube 새 탭 열기

### 목적
영화 상세 페이지에 인라인 YouTube iframe이 페이지를 무겁게 만들고 레이아웃을 차지함. 제거하고, 기존 "시청하기" 버튼 클릭 시 YouTube 새 탭으로 열리도록 변경.

### 현재 상태 확인 (먼저)
- `frontend/app/movies/[id]/page.tsx`에서 트레일러 iframe 위치 확인
- "시청하기" 버튼이 어떤 컴포넌트에 있는지, 현재 동작 확인
- `movie.trailer_key` 데이터 전달 경로 확인

### 구현
1. **인라인 YouTube iframe 영역 전체 삭제** (래퍼 div, 스타일 포함)
2. **시청하기 버튼 수정**:
   - 클릭 → `window.open(`https://www.youtube.com/watch?v=${movie.trailer_key}`, '_blank')`
   - trailer_key가 없는 영화(33.6%) → 버튼 비활성화 또는 숨김
   - 버튼에 외부 링크 느낌 표시 (아이콘 또는 텍스트)
3. **모바일에서도 새 탭 정상 열리는지 확인**

---

## 기능 2: 메인 화면에 "한국 인기 영화" 섹션 추가

### 목적
홈 페이지에 한국 제작 인기 영화 전용 섹션을 추가하여 국내 콘텐츠를 강조.

### 현재 상태 확인 (먼저)
- `frontend/app/page.tsx` (홈 페이지)에서 기존 추천 섹션 구조 확인
- MovieRow 컴포넌트가 어떤 props를 받는지 (title, movies, subtitle 등)
- 백엔드 `GET /api/v1/recommendations`의 섹션 구조 확인
- 백엔드 `GET /api/v1/movies?country=대한민국&sort_by=popularity` 가 이미 동작하는지 확인 (Step 이전에 구현한 country 필터)

### 구현 방법 — 2가지 중 선택

**방법 A: 프론트엔드에서 직접 API 호출 (추천)**
- 홈 페이지에서 `getMovies({ country: "대한민국", sort_by: "popularity", size: 20 })` 호출
- 기존 MovieRow 컴포넌트로 렌더링
- 백엔드 수정 불필요 (country 필터가 이미 구현됨)

**방법 B: 백엔드 recommendations API에 섹션 추가**
- `GET /api/v1/recommendations` 응답에 `korean_popular` 섹션 추가
- DB 쿼리: `WHERE production_countries_ko ILIKE '%대한민국%' ORDER BY popularity DESC`

→ 방법 A가 빠르고 간단하므로 A로 구현. 이미 country 필터가 동작하니 백엔드 수정 없이 프론트만 추가.

### 구현 내용

1. **홈 페이지 (`frontend/app/page.tsx`)**:
   - 기존 섹션들(인기, 높은평점, 날씨, 기분, MBTI, 맞춤) 사이 적절한 위치에 "🇰🇷 한국 인기 영화" 섹션 추가
   - `getMovies({ country: "대한민국", sort_by: "popularity", size: 20 })` 호출
   - 기존 MovieRow 컴포넌트 재사용
   - 섹션 타이틀: "한국 인기 영화" 또는 "🇰🇷 지금 한국에서 인기있는 영화"
   - 서브타이틀 추가 (기존 큐레이션 패턴 참고)

2. **위치**: 인기 영화 바로 다음, 또는 높은 평점 다음 (기존 섹션 순서 확인 후 자연스러운 위치)

3. **데이터 로딩**: 기존 섹션들과 동일한 패턴으로 로딩 (useEffect 또는 서버 fetch)

4. **새로고침 버튼**: 기존 섹션에 🔄 버튼이 있다면 동일하게 추가

### 주의사항
- 기존 홈 페이지 로딩 성능에 영향 최소화 (별도 fetch, 기존 recommendations API 무관)
- 한국 영화가 1,097편이므로 충분한 풀에서 셔플/페이지네이션 가능
- 비로그인 사용자에게도 표시

---

## 완료 조건

### 트레일러
- [ ] 영화 상세 페이지에서 인라인 YouTube iframe 제거됨
- [ ] "시청하기" 버튼 클릭 → YouTube 새 탭 열림
- [ ] trailer_key 없는 영화 → 버튼 비활성화 또는 숨김
- [ ] 모바일 정상 동작

### 한국 인기 영화
- [ ] 홈 페이지에 "한국 인기 영화" 섹션 표시됨
- [ ] 한국 제작 영화가 인기순으로 정렬되어 표시
- [ ] MovieRow 가로 스크롤 정상 동작
- [ ] 비로그인 사용자에게도 표시

---

## 커밋 + 푸시 + 배포

```bash
git add -A
git commit -m "feat: 트레일러 새 탭 열기 + 홈 한국 인기 영화 섹션

- 영화 상세: 인라인 YouTube iframe 제거
- 시청하기 버튼 → window.open YouTube 새 탭
- trailer_key 없는 영화 버튼 비활성화
- 홈 페이지: 한국 인기 영화 섹션 추가 (country=대한민국 필터 활용)
- MovieRow 재사용, 인기순 정렬"

git push origin main
```

배포 후 검증:
- 프로덕션 영화 상세 → 시청하기 클릭 → YouTube 새 탭 확인
- trailer_key 없는 영화 → 버튼 상태 확인
- 프로덕션 홈 → 한국 인기 영화 섹션 표시 + 영화 목록 확인
- CI에서 deploy-frontend (Vercel) 자동 배포 동작 확인

결과를 `claude_results.md`에 저장해줘.