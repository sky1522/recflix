# 유도 섹션(날씨/기분) 헤더 드롭다운 이동 + FeaturedBanner 정리

## 목적
히어로 영역의 fixed 유도 섹션(날씨 4종 + 기분 8종)을 헤더 메뉴 안의 드롭다운으로 이동하여 UX 개선. 히어로 영역은 영화 포스터만 깔끔하게 보이도록 정리.

## 현재 구조 (확인됨)
- 유도 섹션: `FeaturedBanner.tsx` lines 290-414, `position: fixed`, z-40
- 날씨 상태: `useWeather` 훅 (localStorage 캐시 30분)
- 기분 상태: `page.tsx` 로컬 useState + 모듈 캐시
- MBTI: `useAuthStore` Zustand (서버 저장, 프로필에서 설정)
- 추천 연결: `getHomeRecommendations(weather.condition, mood)`

---

## 구현 계획

### Step 1: 기분(Mood) 상태를 Zustand store로 이동

현재 mood가 `page.tsx` 로컬 state라서 헤더에서 접근 불가. Zustand store로 올려야 함.

**새 파일: `frontend/stores/useMoodStore.ts`** (또는 기존 store에 추가)
```typescript
// 참고 구조 — 실제 구현 시 기존 Zustand 패턴(authStore 등) 따를 것
interface MoodStore {
  mood: MoodType | null;
  setMood: (mood: MoodType | null) => void;
}
```

- `page.tsx`의 `useState<MoodType | null>` → `useMoodStore` 로 교체
- `cachedMood` 모듈 레벨 캐시 → store persist 또는 제거
- `page.tsx`의 `useEffect([weather, mood, ...])` 에서 mood를 store에서 가져오도록 변경

**날씨(useWeather)는 이미 훅으로 분리되어 있으므로 헤더에서 그대로 호출 가능. 이동 불필요.**

### Step 2: 헤더에 날씨/기분 드롭다운 추가

**`frontend/components/layout/Header.tsx`** 수정:

**데스크탑 UI:**
- 기존 메뉴(홈, 영화 검색) 우측, 검색바 좌측 영역에 드롭다운 2개 추가
- **날씨 드롭다운**: 현재 날씨 아이콘(☀️/🌧️/☁️/❄️) 표시 + 클릭 시 4종 선택 패널 펼침
  - 선택된 날씨 하이라이트 (ring 또는 배경색)
  - "실시간 날씨로 돌아가기" 버튼 (수동 선택 시만 표시)
  - 현재 기온 표시
- **기분 드롭다운**: 현재 기분 이모지 표시 (미선택 시 😊 기본 아이콘) + 클릭 시 8종 선택 패널 펼침
  - 이모지 + 라벨 표시
  - 토글 방식 (재클릭 시 해제)
  - 선택된 기분 하이라이트

**드롭다운 구현 방식:**
- `useState(isOpen)` + Framer Motion AnimatePresence (기존 프로젝트 패턴)
- 외부 클릭 감지 (useRef + useEffect로 document.addEventListener)
- ESC 키로 닫기
- 다른 드롭다운 열면 기존 드롭다운 자동 닫기

**MBTI는 드롭다운 불필요:**
- 헤더에서 현재 MBTI 표시만 (예: 프로필 아이콘 옆에 "INTJ" 텍스트)
- 클릭 시 /profile로 이동 (기존과 동일)
- MBTI 미설정 시 "MBTI 설정하기" 링크

### Step 3: 모바일 드로어에 날씨/기분 추가

**`frontend/components/layout/HeaderMobileDrawer.tsx`** 수정:

- 기존 날씨 인디케이터 영역을 확장하여 날씨 4종 선택 버튼 추가
- 기분 8종 이모지 그리드 추가 (2×4)
- 터치 타겟 44px 이상 확보
- 선택 시 즉시 반영 (드로어 닫지 않음, 사용자가 직접 닫기)
- 섹션 구분: "날씨 설정", "기분 설정" 라벨 추가

### Step 4: FeaturedBanner 유도 섹션 제거

**`frontend/components/movie/FeaturedBanner.tsx`** 수정:

- lines 290-414 유도 섹션 (fixed 영역) 전체 제거
- 관련 props 정리: `onWeatherChange`, `onMoodChange` 등 FeaturedBanner에서 제거
- FeaturedBanner는 순수하게 영화 포스터 + 미리보기 버튼만 남김
- MBTI 유도 카드(로그인/설정 유도)도 헤더 쪽으로 이동 또는 제거

### Step 5: page.tsx 정리

**`frontend/app/page.tsx`** 수정:

- mood 로컬 state 제거 → `useMoodStore()` 사용
- weather 관련 props를 FeaturedBanner에 더 이상 전달하지 않음
- `useEffect` 의존성에서 mood 소스를 store로 변경
- FeaturedBanner에서 유도 관련 props 전부 제거

---

## 주의사항

1. **홈 페이지 전용 vs 전역**: 날씨/기분 드롭다운은 **모든 페이지**에서 표시. 단, 추천 API 호출은 홈에서만 발생하므로 다른 페이지에서 변경해도 문제없음 (다음에 홈 방문 시 반영)

2. **기존 동작 유지**: 날씨 또는 기분 변경 → 홈 페이지 추천 전체 갱신 (기존과 동일한 useEffect 트리거)

3. **debounce 불필요**: 드롭다운에서 하나씩 선택하는 방식이므로 빠른 연속 토글 가능성 낮음. 필요 시 추후 추가

4. **접근성**: 드롭다운에 aria-expanded, aria-haspopup, role="menu" 적용. 키보드 네비게이션 지원

5. **애니메이션**: Framer Motion으로 드롭다운 열기/닫기 (scale + opacity, 기존 모달 패턴 참고)

6. **z-index**: 헤더 드롭다운이 다른 요소 위에 표시되도록 z-50 이상

---

## 완료 조건

- [ ] 헤더에 날씨 드롭다운: 아이콘 클릭 → 4종 선택 패널
- [ ] 헤더에 기분 드롭다운: 이모지 클릭 → 8종 선택 패널
- [ ] 날씨/기분 선택 시 홈 추천 갱신 (기존과 동일하게 동작)
- [ ] 모바일 드로어에 날씨/기분 선택 UI 포함
- [ ] FeaturedBanner fixed 유도 섹션 완전 제거
- [ ] 히어로 영역 깔끔하게 영화 포스터만 표시
- [ ] 외부 클릭, ESC로 드롭다운 닫기
- [ ] 데스크탑/모바일 모두 정상 동작
- [ ] MBTI 현재 상태 헤더에 표시 + 프로필 링크

---

## 커밋 + 푸시 + 배포

```bash
git add -A
git commit -m "feat: 날씨/기분 유도 UI를 헤더 드롭다운으로 이동

- 헤더: 날씨 드롭다운(4종) + 기분 드롭다운(8종) 추가
- 모바일 드로어: 날씨/기분 선택 UI 추가
- FeaturedBanner: fixed 유도 섹션 완전 제거, 히어로 깔끔하게
- Mood 상태: page.tsx 로컬 → Zustand store로 이동
- 기존 추천 갱신 동작 100% 유지"

git push origin main
```

배포 후 검증:
- 데스크탑: 헤더 날씨/기분 드롭다운 동작 + 추천 갱신 확인
- 모바일: 드로어 내 날씨/기분 선택 동작 확인
- 히어로 영역: 유도 섹션 없이 깔끔한지 확인
- 다른 페이지(/movies, /favorites)에서 헤더 드롭다운 표시 확인

결과를 `claude_results.md`에 저장해줘.