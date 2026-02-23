# Phase 43A: Frontend 성능 — API 클라이언트 내결함성 + 검색 병렬화 결과

## 날짜
2026-02-23

## 변경 파일 목록

| # | 파일 | 주요 변경 |
|---|------|----------|
| 1 | `frontend/lib/api.ts` | ApiError 클래스, fetchAPI timeout/retry/abort 확장 |
| 2 | `frontend/components/search/SearchAutocomplete.tsx` | 키워드+시맨틱 병렬 검색, AbortController stale 응답 차단 |

## 1단계: api.ts fetchAPI 내결함성 강화

### 변경 전 시그니처
```ts
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T>
```

### 변경 후 시그니처
```ts
async function fetchAPI<T>(endpoint: string, options?: FetchAPIOptions): Promise<T>

interface FetchAPIOptions extends Omit<RequestInit, "signal"> {
  timeoutMs?: number;   // 기본 10초
  signal?: AbortSignal; // 외부 취소 시그널
  retry?: boolean;      // GET 5xx/429 재시도 (기본 true)
}
```

### ApiError 클래스
```ts
export class ApiError extends Error {
  status: number;       // HTTP 상태 코드
  retryable: boolean;   // 429/5xx → true
}
```

### 기능 상세

| 기능 | 설명 |
|------|------|
| Timeout | AbortController 기반 10초 기본값, `timeoutMs` 옵션으로 변경 가능 |
| Abort 병합 | `AbortSignal.any()` 지원 시 사용, 미지원 시 수동 이벤트 연결 |
| 재시도 | GET + 5xx/429 → 1초 대기 후 1회 자동 재시도 |
| 재시도 비활성화 | `retry: false` 옵션 또는 POST/PUT/DELETE → 재시도 안 함 |
| AbortError | DOMException AbortError는 별도 분기, 재시도하지 않음 |
| 하위 호환 | 기존 `fetchAPI(endpoint)` / `fetchAPI(endpoint, { method: "POST" })` 그대로 동작 |

### signal 지원 추가 함수
- `searchAutocomplete(query, limit?, signal?)` — 선택적 signal 파라미터 추가
- `semanticSearch(query, limit?, signal?)` — 선택적 signal 파라미터 추가
- 기존 호출 코드 변경 불필요 (optional 파라미터)

## 2단계: SearchAutocomplete 검색 병렬화

### 변경 전 (직렬)
```
1. await searchAutocomplete(query)     ← 키워드 완료 대기
2. setResults(data)
3. if (NL) await semanticSearch(query)  ← 시맨틱 완료 대기
4. setSemanticResults(data)
총 소요: 키워드 지연 + 시맨틱 지연 (직렬)
```

### 변경 후 (병렬 + abort)
```
1. Promise.allSettled([keyword, semantic])  ← 동시 실행
2. signal.aborted 체크 → stale이면 무시
3. 각 결과 독립 처리 (fulfilled/rejected)
총 소요: max(키워드 지연, 시맨틱 지연) (병렬)
```

### AbortController 적용
- 새 입력(debouncedQuery 변경) 시 이전 요청의 AbortController.abort() 호출
- useEffect cleanup 함수에서 abort
- AbortError는 console.error로 출력하지 않음 (DOMException 체크)
- abort signal을 `searchAutocomplete()`과 `semanticSearch()`에 전달 → 실제 HTTP 요청도 취소

## 검증 결과
- `tsc --noEmit`: 0 errors
- `npm run build`: 성공 (13/13 pages)
- `npm run lint`: 0 ESLint errors
- fetchAPI 하위 호환: 기존 24개 API 함수 시그니처 변경 없음
