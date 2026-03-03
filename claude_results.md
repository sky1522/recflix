# 프로젝트 문서 동기화

> 작업일: 2026-03-03

## Phase 1: 갭 목록

### CLAUDE.md (핵심 구조 섹션)
| 갭 | 유형 | 설명 |
|---|------|------|
| `settings/page.tsx` 누락 | 신규 파일 | 설정 페이지 (닉네임, MBTI, 장르, 테마, 계정) |
| `themeStore.ts` 누락 | 신규 파일 | Zustand 테마 스토어 (dark/light) |
| `useMoodStore.ts` 누락 | 신규 파일 | Zustand 기분 스토어 |
| `ThemeProvider.tsx` 누락 | 신규 파일 | 테마 클래스 적용 래퍼 |
| `MBTIModal.tsx` 누락 | 기존 파일 | MBTI 선택 모달 (설정 페이지에서 사용) |
| `HeaderMobileDrawer.tsx` 누락 | 기존 파일 | 모바일 네비게이션 드로어 |
| `searchUtils.ts` 누락 | 기존 파일 | 검색 유틸리티 |
| `HighlightText.tsx` 경로 오류 | 경로 | `search/` → `ui/` |
| `Skeleton.tsx` 경로 오류 | 경로 | 미기재 → `ui/Skeleton.tsx` |
| `docs/DECISION.md` 누락 | 문서 | 아키텍처 결정 기록 |
| `docs/DATA_PREPROCESSING.md` 누락 | 문서 | 데이터 전처리 문서 |
| `Header.tsx` 설명 오래됨 | 설명 | 날씨/기분/MBTI 드롭다운 + 프로필 드롭다운 |
| `profile/page.tsx` 설명 오래됨 | 설명 | 프로필 + MBTI 변경 → 프로필 정보 + 설정 링크 |
| stores 섹션 불완전 | 설명 | 2개 → 4개 (+ themeStore, useMoodStore) |

### PROGRESS.md
| 갭 | 설명 |
|---|------|
| Phase 54 누락 | 트레일러 + 한국 인기 영화 + 날씨/기분/MBTI 헤더 드롭다운 + 다크/라이트 모드 + 설정 페이지 |
| 프로젝트 구조 오래됨 | settings, theme, mood, drawer 등 신규 파일 다수 누락 |
| 최종 업데이트 날짜 | 2026-02-27 → 2026-03-03 |

### frontend-patterns.md (스킬)
| 갭 | 설명 |
|---|------|
| Zustand 스토어 수 | "2개" → "4개" (+ themeStore, useMoodStore) |
| 테마 시스템 패턴 누락 | CSS 변수 기반 시맨틱 토큰, ThemeProvider, FOUC 방지 |
| 드롭다운 패턴 누락 | 헤더 날씨/기분/MBTI/프로필 4종 드롭다운 |
| 게스트 MBTI 패턴 누락 | localStorage 기반 비로그인 MBTI 저장 |

### HANDOFF_CONTEXT.md
| 갭 | 설명 |
|---|------|
| Phase 54 미반영 | 설정 페이지, 테마, MBTI 드롭다운, 프로필 드롭다운 |
| 프론트엔드 구조 불완전 | 신규 파일(settings, theme, mood) 미기재 |

### ARCHITECTURE.md
| 갭 | 설명 |
|---|------|
| Client 섹션 Zustand 스토어 | themeStore, useMoodStore 누락 |
| 다크/라이트 모드 미기재 | CSS 변수 기반 테마 시스템 |

## Phase 2: 수정 대상
1. CLAUDE.md — 핵심 구조 + stores 섹션 업데이트
2. PROGRESS.md — Phase 54 추가 + 프로젝트 구조 업데이트
3. frontend-patterns.md — 테마/드롭다운/게스트MBTI 패턴 추가
4. HANDOFF_CONTEXT.md — 프론트엔드 구조 업데이트
5. ARCHITECTURE.md — Client 섹션 Zustand 추가
