# 프롬프트 2: movies/[id]/page.tsx 리팩토링 (622줄 → 500줄 이하)

영화 상세 페이지 컴포넌트 분리. 기능 변경 없이 구조만 분리. 충분히 탐색하고 시작해.

⚠️ 프롬프트 1 (recommendations.py 리팩토링) 완료 후 실행할 것.

먼저 읽을 것:
- .claude/skills/code-quality.md (파일 크기 규칙, 분리 기준)
- .claude/skills/frontend-patterns.md (컴포넌트 구조, 훅 패턴)
- frontend/app/movies/[id]/page.tsx (전체 구조 파악 — grep으로 컴포넌트/섹션부터)

```bash
# 컴포넌트/함수 목록 확인
grep -n "function \|const .* = " frontend/app/movies/\[id\]/page.tsx | head -30

# JSX 섹션 경계 확인
grep -n "return\|<section\|<div className.*container\|{/\*" frontend/app/movies/\[id\]/page.tsx

# import 확인
head -30 frontend/app/movies/\[id\]/page.tsx

# 이 페이지에서 사용하는 컴포넌트/훅
grep -n "import " frontend/app/movies/\[id\]/page.tsx
```

---

=== 1단계: Research ===

page.tsx의 UI 구조를 파악:

1. 렌더링하는 주요 섹션 (히어로 배너, 영화 정보, 출연진, 유사 영화, 캐치프레이즈 등)
2. 사용하는 state/effect 목록
3. 내부 헬퍼 함수 목록
4. 각 섹션의 대략적 줄 범위

---

=== 2단계: Plan ===

아래 분리 방향을 기반으로 구체적 계획 수립:

**새 파일 생성 (frontend/app/movies/[id]/ 하위):**
- `components/MovieHero.tsx` — 히어로 배너 (포스터, 제목, 캐치프레이즈, 기본 정보, 평점/찜 버튼)
- `components/MovieInfo.tsx` — 상세 정보 (줄거리, 감독, 제작국, 장르, 등급, 러닝타임 등)
- `components/MovieCast.tsx` — 출연진 목록
- `components/SimilarMovies.tsx` — 유사 영화 섹션

또는 실제 코드 구조에 따라 더 자연스러운 경계로 분리. 핵심은:
- page.tsx에는 데이터 페칭 + 레이아웃 조합만 남김
- 각 서브 컴포넌트는 props로 데이터 받음
- 상태 관리(평점, 찜)는 page.tsx에서 관리하고 props로 전달

**목표:** page.tsx 300줄 이하, 서브 컴포넌트 각각 150줄 이하

실제 코드를 확인한 후 자연스러운 경계에서 분리. 억지로 나누지 말 것.

---

=== 3단계: Implement ===

계획대로 구현. 주의사항:

1. **기능 변경 절대 금지** — 순수 리팩토링만
2. **'use client'** 지시문 필요한 컴포넌트에 추가
3. Framer Motion 애니메이션 유지
4. 반응형 CSS 클래스 유지 (모바일/데스크톱)
5. interactionStore 연동 유지 (평점, 찜)
6. 동적 OG 메타태그는 layout.tsx에 있으므로 건드리지 않음
7. 에러 바운더리 (error.tsx)도 건드리지 않음

---

=== 건드리지 말 것 ===
- backend/ 전체
- frontend/app/movies/[id]/layout.tsx (OG 메타태그)
- frontend/app/movies/[id]/error.tsx (에러 바운더리)
- frontend/app/ 중 movies/[id]/page.tsx 외 다른 페이지
- frontend/components/ 기존 컴포넌트 (MovieCard, MovieRow, MovieModal 등)
- frontend/stores/, hooks/, lib/
- 모든 .md 문서 파일

---

=== 검증 ===
```bash
# 파일별 줄 수 확인
wc -l frontend/app/movies/\[id\]/page.tsx
wc -l frontend/app/movies/\[id\]/components/*.tsx

# TypeScript 타입 체크
cd frontend && npx tsc --noEmit

# ESLint
cd frontend && npx next lint

# 빌드 확인
cd frontend && npm run build
```

---

결과를 claude_results.md에 **기존 내용 아래에 --- 구분선 후 이어서** 저장:

```markdown
---

# movies/[id]/page.tsx 리팩토링 결과

## 날짜
YYYY-MM-DD

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| movies/[id]/components/MovieHero.tsx | 히어로 배너 | N줄 |
| movies/[id]/components/MovieInfo.tsx | 상세 정보 | N줄 |
| movies/[id]/components/MovieCast.tsx | 출연진 | N줄 |
| movies/[id]/components/SimilarMovies.tsx | 유사 영화 | N줄 |

## 수정된 파일
| 파일 | 변경 내용 | 줄 수 변화 |
|------|----------|-----------|
| movies/[id]/page.tsx | 데이터 페칭 + 레이아웃만 남김 | 622줄 → N줄 |

## 분리 결과
| 파일 | 줄 수 | 역할 |
|------|-------|------|
| page.tsx | N줄 | 데이터 페칭 + 레이아웃 조합 |
| MovieHero.tsx | N줄 | 히어로 배너 |
| MovieInfo.tsx | N줄 | 상세 정보 |
| MovieCast.tsx | N줄 | 출연진 |
| SimilarMovies.tsx | N줄 | 유사 영화 |
| **합계** | N줄 | (622줄에서 변화) |

## 검증 결과
- TypeScript: No errors ✅
- ESLint: No warnings ✅
- Build: 성공 ✅
- 기능 변경: 없음 ✅
```

git add -A && git commit -m 'refactor(frontend): movies/[id]/page.tsx 서브 컴포넌트 분리' && git push origin HEAD:main