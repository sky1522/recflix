# 조사: 프로필 페이지 MBTI 선택 — 저장/닫기 버튼 누락

> 조사일: 2026-03-03
> 수정 없음 (읽기 전용 조사)

## 사용자 보고 흐름

```
헤더 우측 프로필 버튼 → 로그인 → 프로필 페이지 → MBTI 선택
→ "팝업창에 저장 또는 X(닫기) 버튼 없음"
```

## 발견 사항 (심각도순)

### 1. [높음] 프로필 페이지에 X(닫기) 버튼 없음

**파일**: `frontend/app/profile/page.tsx`
**전체 125줄, X 버튼 관련 코드 없음**

로그인/회원가입 페이지는 X 버튼이 있으나, 프로필 페이지에는 없음:

| 페이지 | X 버튼 | 위치 |
|--------|--------|------|
| `login/page.tsx:59-65` | **있음** | `<button onClick={() => router.back()}>` + `<X>` 아이콘 |
| `signup/page.tsx:75-81` | **있음** | `<button onClick={() => router.back()}>` + `<X>` 아이콘 |
| `profile/page.tsx` | **없음** | 닫기/뒤로가기 버튼 일체 없음 |

사용자가 프로필 페이지에서 빠져나가려면 **브라우저 뒤로가기** 또는 **헤더 로고/메뉴**를 클릭해야 함.

### 2. [높음] MBTI 저장 버튼 없음 — 자동 저장이지만 피드백 부족

**파일**: `frontend/app/profile/page.tsx:36-46`

```tsx
const handleMBTIChange = async (mbti: string) => {
  setSelectedMBTI(mbti);
  setSaving(true);
  try {
    await updateMBTI(mbti);     // 클릭 즉시 API 호출
  } catch (error) { ... }
  finally { setSaving(false); }
};
```

현재 동작:
- MBTI 버튼 클릭 → 즉시 `updateMBTI(mbti)` API 호출 → 서버 저장
- 명시적 "저장" 버튼 **없음**
- 저장 중일 때 유일한 피드백: `"저장 중..."` 텍스트 (line 103-105)
- 저장 완료 시 피드백 **없음** (토스트/알림 없음)
- 사용자는 저장이 되었는지 알 수 없음

비교: 일반적인 설정 페이지 UX는 명시적 "저장" 버튼 또는 "저장 완료" 토스트를 제공

### 3. [중간] 프로필 페이지 레이아웃 구조 — 다른 폼 페이지와 불일치

| 속성 | login | signup | profile |
|------|-------|--------|---------|
| X 닫기 버튼 | O | O | **X** |
| 카드 컨테이너 | `bg-dark-100 rounded-xl p-6` | `bg-dark-100 rounded-lg p-8` | `bg-dark-100 rounded-lg p-8` |
| 위치 | 화면 중앙 | 화면 중앙 | 상단 정렬 (py-12) |
| 명시적 저장 | N/A | "회원가입" 버튼 | **없음** (자동 저장) |
| 성공 피드백 | 홈 리다이렉트 | 홈 리다이렉트 | **없음** |

### 4. [낮음] 헤더에서 프로필까지의 진입 경로

**비로그인 상태**:
- 헤더 "로그인" 버튼 (`Header.tsx:275`) → `/login` → 로그인 성공 → `/` 홈 리다이렉트
- 이후 헤더 프로필 아이콘 (`Header.tsx:263`) → `/profile`
- 또는 헤더 MBTI 배지 (`Header.tsx:240-249`) → `/profile`

**로그인 상태**:
- 헤더 프로필 아이콘 → `/profile`
- 헤더 MBTI 배지 "MBTI 설정" → `/profile`
- 모바일 드로어 프로필 영역 (`HeaderMobileDrawer.tsx:215`) → `/profile`

모든 경로가 `/profile` 전체 페이지로 이동. **모달/팝업은 없음** — 사용자가 "팝업"이라고 인지한 것은 프로필 페이지 자체.

## 영향 범위

| 파일 | 수정 필요 여부 | 이유 |
|------|--------------|------|
| `frontend/app/profile/page.tsx` | **필수** | X 버튼 + 저장 피드백 추가 |
| `frontend/components/layout/Header.tsx` | 불필요 | MBTI 배지 → /profile 링크, 정상 동작 |
| `frontend/components/layout/HeaderMobileDrawer.tsx` | 불필요 | 프로필 링크 정상 |

## 구현 방향 (수정하지 않음, 방향만 나열)

### 방향 A: 프로필 페이지에 X 버튼 + 저장 피드백 추가
- 우상단에 X 닫기 버튼 (login/signup과 동일 패턴)
- MBTI 자동 저장 유지 + 저장 완료 시 체크마크 또는 토스트 표시
- 최소 변경, 기존 패턴 일관성

### 방향 B: MBTI 선택을 모달로 변경
- 헤더 MBTI 배지 클릭 시 모달 팝업으로 MBTI 16종 표시
- 모달에 저장 + X 닫기 버튼
- /profile 이동 없이 인라인 변경
- 변경 범위 더 큼 (Header에 모달 추가)

### 방향 C: 프로필 페이지 전면 리뉴얼
- X 버튼, 저장 확인 버튼, 성공 토스트
- MBTI 선택 + 저장 버튼 분리 (자동 저장 제거)
- 가장 전통적인 폼 UX

## 참고 파일 목록

- `frontend/app/profile/page.tsx` — MBTI 선택 UI (125줄)
- `frontend/app/login/page.tsx:59-65` — X 닫기 버튼 참고 패턴
- `frontend/app/signup/page.tsx:75-81` — X 닫기 버튼 참고 패턴
- `frontend/stores/authStore.ts:88-95` — `updateMBTI()` 함수
- `frontend/components/layout/Header.tsx:240-249` — MBTI 배지 (새로 추가됨)
