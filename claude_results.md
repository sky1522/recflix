# Phase 52B: A/B 리포트 통계 유의성 + 추가 메트릭

**날짜**: 2026-02-25
**커밋**: `4831cd5`

---

## 1. 통계 검증 구현 방식

### Z-test for Proportions (두 비율 비교)

```
z = (p₁ - p₂) / √(p_pool × (1 - p_pool) × (1/n₁ + 1/n₂))
p_pool = (x₁ + x₂) / (n₁ + n₂)
p_value = 2 × (1 - Φ(|z|))    [two-tailed]
```

- **Φ(x)**: `math.erf` 기반 표준 정규 CDF (scipy 불필요)
- **최소 표본**: 그룹당 30건 미만 시 `(None, None)` 반환 → `note: "insufficient_data"`
- **유의 수준**: α = 0.05

### Wilson Score 95% 신뢰구간

```
center = (p̂ + z²/2n) / (1 + z²/n)
margin = z × √((p̂(1-p̂) + z²/4n) / n) / (1 + z²/n)
CI = [center - margin, center + margin]
```

- Wald interval보다 소표본에서 안정적
- z = 1.96 (95%)

### 검증 결과 (알려진 값)

| 테스트 | 기대값 | 실제값 |
|--------|--------|--------|
| normal_cdf(0) | 0.5 | 0.5 |
| normal_cdf(1.96) | ~0.975 | 0.975002 |
| Z-test(50/1000 vs 70/1000) | z≈-1.88, p≈0.06 (비유의) | z=-1.8831, p=0.059686 |
| n<30 → None | (None, None) | (None, None) |

---

## 2. 추가된 메트릭 목록

| 메트릭 | 필드 | SQL/계산 방식 |
|--------|------|--------------|
| **CTR 신뢰구간** | `ctr_ci_lower`, `ctr_ci_upper` | Wilson score CI |
| **추천 수용률** | `avg_rating_from_recs` | source_section ≠ 'direct'인 rating 이벤트의 평균 평점 |
| **재방문율** | `return_rate` | 2일+ 활성인 사용자 비율 |
| **세션 이벤트** | `avg_session_events` | session_id별 이벤트 수 평균 |
| **전환 퍼널** | `funnel` | impression→click→detail→rating/favorite 단계별 전환율 |
| **통계 비교** | `comparisons[]` | CTR/rating_conv/favorite_conv 그룹 쌍별 Z-test |
| **일별 활성** | `daily_active_users` | 그룹별 일별 고유 사용자 수 |

---

## 3. 그룹 비율 조절 방식

### 환경변수

```
EXPERIMENT_WEIGHTS=control:34,test_a:33,test_b:33   # 기본값
EXPERIMENT_WEIGHTS=control:80,test_a:10,test_b:10   # 보수적 실험
```

### 구현

- `config.py`: `EXPERIMENT_WEIGHTS: str` 설정 추가
- `auth.py`: `_weighted_random_group()` — `random.choices(groups, weights)` 사용
- 파싱 실패 시 `random.choice(EXPERIMENT_GROUPS)` 폴백
- 3곳 적용: 이메일 가입, 카카오 가입, 구글 가입

### 검증

10,000회 샘플링 (34:33:33 가중치):
- control: 34.0%, test_a: 33.6%, test_b: 32.3% — 설정대로 분배

---

## 4. ABReport 스키마 변경

### 전 (Phase 52A 이전)

```json
{
  "period": "7d",
  "groups": {
    "control": {
      "users": 10,
      "total_clicks": 50,
      "total_impressions": 200,
      "ctr": 0.25,
      "avg_detail_duration_ms": 15000,
      "rating_conversion": 0.1,
      "favorite_conversion": 0.05,
      "by_section": {}
    }
  },
  "winner": "control",
  "confidence_note": "..."
}
```

### 후 (Phase 52B)

```json
{
  "period": "7d",
  "groups": {
    "control": {
      "users": 10,
      "total_clicks": 50,
      "total_impressions": 200,
      "ctr": 0.25,
      "ctr_ci_lower": 0.1978,
      "ctr_ci_upper": 0.3098,
      "avg_detail_duration_ms": 15000,
      "rating_conversion": 0.1,
      "favorite_conversion": 0.05,
      "by_section": {},
      "avg_rating_from_recs": 3.8,
      "return_rate": 0.45,
      "avg_session_events": 12.3,
      "funnel": {
        "impressions": 200,
        "clicks": 50,
        "click_rate": 0.25,
        "detail_views": 40,
        "detail_rate": 0.8,
        "ratings": 4,
        "rating_rate": 0.1,
        "favorites": 2,
        "favorite_rate": 0.05
      }
    }
  },
  "winner": "control",
  "confidence_note": "통계적 유의성은 comparisons 필드의 p_value/significant 참조",
  "comparisons": [
    {
      "group_a": "control",
      "group_b": "test_a",
      "metric": "ctr",
      "value_a": 0.25,
      "value_b": 0.20,
      "difference": 0.05,
      "z_statistic": 1.23,
      "p_value": 0.218,
      "significant": false,
      "note": null
    }
  ],
  "minimum_sample_note": "각 그룹 최소 노출 수: 200. CTR Z-test는 그룹당 최소 30건 필요...",
  "daily_active_users": {
    "control": {"2026-02-20": 5, "2026-02-21": 3}
  }
}
```

---

## 5. 변경 파일 목록

| 파일 | 변경 |
|------|------|
| `backend/app/api/v1/ab_stats.py` | **NEW** — Z-test, Wilson CI, 추가 메트릭 SQL 쿼리 |
| `backend/app/schemas/user_event.py` | ABComparison 추가, ABGroupStats/ABReport 필드 확장 |
| `backend/app/api/v1/events.py` | ab-report 리팩토링 + 헬퍼 함수 분리 + 신규 메트릭 |
| `backend/app/config.py` | EXPERIMENT_WEIGHTS 설정 추가 |
| `backend/app/api/v1/auth.py` | _weighted_random_group() + 3곳 적용 |

## 검증 결과

| 항목 | 결과 |
|------|------|
| `ruff check app/` | All checks passed |
| `python -c 'from app.main import app'` | RecFlix (import 성공) |
| `pytest -v --tb=short` | 10 passed, 4 skipped |
| Z-test 수동 검증 | 기대값 일치 |
| 가중치 그룹 배정 | 10000회 샘플링 — 34/34/32% |
| git push | 성공 |
