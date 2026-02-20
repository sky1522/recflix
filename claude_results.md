# Phase 37: 추천 이유 생성 — 템플릿 기반 구현 결과

## 날짜
2026-02-20

## 생성/수정된 파일 목록

| 파일 | 작업 | 줄 수 |
|------|------|-------|
| `backend/app/api/v1/recommendation_reason.py` | **신규 생성** | 228줄 |
| `backend/app/schemas/recommendation.py` | `recommendation_reason` 필드 추가 | +3줄 |
| `backend/app/api/v1/recommendations.py` | `generate_reason()` 호출 연동 | +6줄 |
| `frontend/types/index.ts` | `HybridMovie` 타입 확장 | +1줄 |
| `frontend/components/movie/HybridMovieCard.tsx` | 추천 이유 텍스트 표시 | +6줄 |

## generate_reason 테스트 결과

| # | 컨텍스트 | 생성된 추천 이유 |
|---|---------|----------------|
| 1 | INTJ + rainy + relaxed | `INTJ이(가) 비 오는 날에 보면 더 좋은 영화` |
| 2 | tense mood (#긴장감 태그) | `손에 땀을 쥐게 하는 긴장감이 매력이에요` |
| 3 | quality (#명작 태그) | `시간이 지나도 빛나는 클래식 명작` |
| 4 | personal + quality 복합 | `취향에 딱 맞으면서 평점도 높은 영화예요` |
| 5 | snowy 날씨 | `눈 오는 날 포근하게 감싸주는 영화예요` |
| 6 | 빈 태그 + weather+mood | `비 오는 날 편안한 기분에 완벽한 선택이에요` |

## API 응답 예시

```json
{
  "hybrid_row": {
    "title": "🎯 INTJ + 🌧️ + 😌 맞춤 추천",
    "movies": [
      {
        "id": 278,
        "title_ko": "쇼생크 탈출",
        "recommendation_tags": [
          {"type": "mbti", "label": "#INTJ추천", "score": 0.85},
          {"type": "weather", "label": "#비오는날", "score": 0.7}
        ],
        "hybrid_score": 0.82,
        "recommendation_reason": "INTJ이(가) 비 오는 날에 보면 더 좋은 영화"
      }
    ]
  }
}
```

## Frontend UI 동작

- `HybridMovieCard` 컴포넌트에서 추천 태그 뱃지 아래에 표시
- 스타일: `text-xs text-white/50 italic line-clamp-2`
- `recommendation_reason`이 빈 문자열이면 표시하지 않음
- 최대 2줄, 넘치면 `...` 처리

```
┌──────────────┐
│   포스터      │
│     82%      │  ← hybrid_score
├──────────────┤
│ 쇼생크 탈출   │
│ 1994 · 드라마 │
│ #INTJ추천    │  ← 태그 뱃지
│ #비오는날     │
│ INTJ이(가) 비 │  ← ★ 추천 이유 (NEW)
│ 오는 날에...  │
└──────────────┘
```

## 검증 결과

| 검증 항목 | 결과 |
|----------|------|
| `ruff check recommendation_reason.py` | **PASS** |
| `ruff check recommendations.py` | **PASS** |
| generate_reason 단위 테스트 (6개 시나리오) | **PASS** |
| Frontend `npm run build` | **PASS** |
| GitHub Actions CI (Lint + Build) | **PASS** |
| GitHub Actions CD (Railway Deploy) | **PASS** |
| 프로덕션 헬스체크 | **PASS** (all components healthy) |

## 프로덕션 배포

- GitHub Actions CD가 자동으로 Railway에 배포 완료
- Vercel도 GitHub 연동으로 Frontend 자동 배포 완료
- 추가 수동 배포 불필요

## 기술 요약

- **43개 템플릿**: MBTI 11 + Weather 12 + Mood 10 + Quality 4 + 복합 6
- **우선순위**: 복합조건 > Mood/Personal > MBTI > Weather > Quality
- **비용**: $0 (LLM 호출 없음)
- **지연**: 0ms (문자열 조합)
- **다양성**: 같은 조건에 여러 템플릿이면 `random.choice`로 변주
