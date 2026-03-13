# 시연 품질 개선 2건 수정

시연 발표 전 마지막 품질 개선입니다. 아래 2건을 수정해주세요.

---

## 이슈 1: 헤더 날씨 표시에 도시명 누락 (⚠️ 시연 영향)

### 현재 상태
- 헤더 날씨 버튼: 이모지 + 온도만 표시 (예: "☁️ 14°C")
- 기대 형태: "수원시 · 흐림 14°C"
- WeatherIndicator 컴포넌트가 정의되어 있지만 헤더에서 사용되지 않음
- 시연 시 "위치 정보가 작동하는지" 청중이 확인할 수 없음

### 관련 파일
- frontend/components/layout/Header.tsx:251-252 (현재 temperature만 렌더링)
- frontend/components/weather/WeatherBanner.tsx:184 (WeatherIndicator 정의)
- frontend/hooks/useWeather.ts (weather 객체에 city, description_ko 포함)

### 수정 사항
Header.tsx의 날씨 버튼 영역 수정:
1. 현재: `{weather.icon} {weather.temperature}°C`
2. 변경: `{weather.city} · {weather.description_ko} {weather.temperature}°C`
3. 공간이 부족하면 축약: `{weather.city} {weather.temperature}°C` (도시명 + 온도)
4. weather.city가 null/undefined인 경우 기존 표시(이모지+온도)로 fallback

### 모바일 대응
- HeaderMobileDrawer.tsx에도 동일하게 적용
- 모바일은 공간이 좁으므로 `{weather.city} {weather.temperature}°C` 축약형 사용

### 검증
- 위치 허용 시: "수원시 · 흐림 14°C" 형태로 표시
- 위치 거부 시: 기존 이모지+온도 표시 유지 (또는 "서울" 기본값)
- 날씨 드롭다운에서 수동 변경 시에도 도시명 유지

---

## 이슈 2: MovieModal에서 장르/키워드 태그 클릭 시 검색 이동 없음 (⚠️ 시연 영향)

### 현재 상태
- 영화 상세 페이지(/movies/[id]): 장르/키워드가 클릭 가능한 링크 → 검색 페이지 이동 ✅
- MovieModal(홈에서 영화 클릭 시 팝업): 장르가 단순 텍스트 칩, 키워드 UI 없음 ❌
- 시연 시나리오 ⑥에서 "장르 태그 클릭 → 검색 이동"을 보여줘야 하는데, 모달에서는 불가

### 관련 파일
- frontend/components/movie/MovieModal.tsx:233, 240 (장르가 단순 span)
- frontend/app/movies/[id]/components/MovieHero.tsx:180 (장르 링크 구현 — 참고 패턴)
- frontend/app/movies/[id]/components/MovieSidebar.tsx:64 (키워드 링크 구현 — 참고 패턴)

### 수정 사항

1. MovieModal.tsx의 장르 표시 부분:
   - 현재: `<span className="...">{genre.name}</span>` (단순 텍스트)
   - 변경: 클릭 시 모달을 닫고 `/movies?genre={genre.id}` 로 이동
   - MovieHero.tsx:180의 장르 링크 패턴을 참고하여 동일하게 구현
   - 스타일: 기존 칩 스타일 유지하되 cursor-pointer + hover 효과 추가

2. 키워드 표시 추가 (선택사항, 시간 되면):
   - 영화 상세 데이터에 keywords가 포함되어 있다면 모달에도 표시
   - MovieSidebar.tsx:64 패턴 참고
   - 클릭 시 `/movies?keyword={keyword.id}` 로 이동

3. 모달 닫기 처리:
   - 태그 클릭 → 모달 닫기(onClose 호출) → router.push 실행
   - 모달이 닫히지 않은 채 페이지가 이동하면 안 됨

### 검증
- 홈에서 영화 클릭 → 모달 열림 → 장르 "애니메이션" 클릭 → 모달 닫힘 → /movies?genre=16 이동
- 상세 페이지의 장르 링크도 기존대로 작동 (회귀 테스트)

---

## 완료 후
- 커밋 분리:
  1. "feat: display city name in weather header button"
  2. "feat: add clickable genre tags to MovieModal"
- push 및 Vercel 배포 확인
- 시연 시나리오 전체 재점검
- 결과를 claude_results.md에 기록