# Phase 4-1: A/B 테스트 프레임워크 + 추천 품질 대시보드

Phase 3의 CF 모델을 실사용자 대상으로 검증할 수 있는 실험 인프라 구축.

⚠️ Phase 2 (이벤트 로깅) + Phase 3 (CF 모델) 완료 후 실행.

먼저 읽을 것:
- CLAUDE.md
- .claude/skills/database.md (DB 스키마 규칙)
- .claude/skills/recommendation.md (추천 엔진 구조)
- backend/app/models/user.py (현재 User 모델)
- backend/app/api/v1/recommendation_engine.py (현재 스코어링)
- backend/app/api/v1/recommendation_constants.py (가중치 상수)
- backend/app/api/v1/events.py (이벤트 API, 통계 엔드포인트)

현재 상태 파악:
```bash
# User 모델 구조
grep -n "class User\|Column" backend/app/models/user.py

# 현재 추천 엔드포인트 파라미터
grep -n "def \|async def " backend/app/api/v1/recommendations.py | head -10

# 이벤트 통계 엔드포인트
grep -n "def \|stats" backend/app/api/v1/events.py
```

---

=== 1단계: User 모델에 실험 그룹 추가 ===

**users 테이블에 컬럼 추가:**

```python
# User 모델에 추가
experiment_group = Column(String(10), default="control", nullable=False)
# 값: "control" (기존 Rule-based), "test_a" (Hybrid α=0.5), "test_b" (Hybrid α=0.3)
```

**신규 사용자 자동 배정:**
- 회원가입 시 랜덤 배정 (3등분)
- auth.py의 register 엔드포인트에서 `random.choice(["control", "test_a", "test_b"])` 추가

**기존 사용자 배정 (마이그레이션):**
```sql
-- 기존 사용자를 3등분으로 랜덤 배정
UPDATE users SET experiment_group = 
  CASE (id % 3)
    WHEN 0 THEN 'control'
    WHEN 1 THEN 'test_a'
    WHEN 2 THEN 'test_b'
  END
WHERE experiment_group IS NULL;
```

---

=== 2단계: 추천 API에 실험 그룹 분기 ===

**recommendation_engine.py 수정:**

```python
def get_weights_for_group(experiment_group: str) -> dict:
    """실험 그룹별 다른 가중치 반환"""
    if experiment_group == "test_a":
        return WEIGHTS_HYBRID_A  # Rule 0.5 + CF 0.5
    elif experiment_group == "test_b":
        return WEIGHTS_HYBRID_B  # Rule 0.3 + CF 0.7
    else:  # "control"
        return WEIGHTS_WITHOUT_CF  # 기존 Rule-based만
```

**recommendation_constants.py에 실험 가중치 추가:**

```python
# A/B 테스트 가중치
WEIGHTS_HYBRID_A = {
    "mbti": 0.12, "weather": 0.10, "mood": 0.15, "personal": 0.13, "cf": 0.50,
}
WEIGHTS_HYBRID_B = {
    "mbti": 0.08, "weather": 0.07, "mood": 0.10, "personal": 0.05, "cf": 0.70,
}
```

**recommendations.py 수정:**
- `current_user.experiment_group`을 가져와서 엔진에 전달
- 비로그인 사용자는 항상 "control"

---

=== 3단계: 이벤트에 실험 그룹 기록 ===

**events.py 수정:**

이벤트 기록 시 `metadata`에 `experiment_group` 자동 포함:

```python
@router.post("/events")
async def create_event(...):
    ...
    # 실험 그룹 자동 추가
    metadata = event.metadata or {}
    if current_user:
        metadata["experiment_group"] = current_user.experiment_group
    db_event.metadata_ = metadata
    ...
```

---

=== 4단계: 추천 품질 대시보드 API ===

**backend/app/api/v1/events.py의 stats 엔드포인트 확장** 또는 별도 엔드포인트:

```
GET /api/v1/events/ab-report?days=7
```

반환:
```json
{
  "period": "7d",
  "groups": {
    "control": {
      "users": 150,
      "total_clicks": 500,
      "total_impressions": 3000,
      "ctr": 0.167,
      "avg_detail_duration_ms": 32000,
      "rating_conversion": 0.05,
      "favorite_conversion": 0.08,
      "by_section": {
        "weather": {"clicks": 120, "impressions": 800, "ctr": 0.15},
        "mbti": {"clicks": 90, "impressions": 750, "ctr": 0.12},
        "mood": {"clicks": 180, "impressions": 900, "ctr": 0.20},
        "personal": {"clicks": 110, "impressions": 550, "ctr": 0.20}
      }
    },
    "test_a": { ... },
    "test_b": { ... }
  },
  "winner": "test_a",  // CTR 기준 최고 그룹 (참고용, 통계적 유의성 미포함)
  "confidence_note": "통계적 유의성 검증은 최소 1000명 이상, 2주 이상 데이터 필요"
}
```

**집계 SQL 예시:**
```sql
SELECT 
  metadata->>'experiment_group' as exp_group,
  event_type,
  COUNT(*) as count,
  COUNT(DISTINCT user_id) as unique_users
FROM user_events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY exp_group, event_type
ORDER BY exp_group, event_type;
```

---

=== 5단계: "관심없음" 버튼 ===

추천 카드에 부정적 시그널 수집용 버튼 추가.

**Backend:**
- event_type 목록에 `"not_interested"` 추가 (schemas/user_event.py의 allowed set)
- 별도 API 필요 없음 (기존 이벤트 API로 충분)

**Frontend (가이드만, 프롬프트에서 직접 구현하지 않아도 됨):**
- MovieCard에 X 버튼 또는 "..." 메뉴에 "관심없음" 옵션
- 클릭 시 `trackEvent({ event_type: "not_interested", movie_id, metadata: { section } })`
- 카드를 UI에서 숨기기 (선택)

---

=== 건드리지 말 것 ===
- frontend/ UI/스타일 (이번은 API + 데이터 레이어만)
- 기존 추천 로직의 비즈니스 규칙 (가중치만 분기, 로직 변경 금지)
- recommendation_cf.py (Phase 3-2에서 완성)
- 모든 .md 문서 파일

---

=== 검증 ===
```bash
# User 모델에 experiment_group 확인
python -c "from app.models.user import User; print(hasattr(User, 'experiment_group'))"

# 가중치 분기 확인
python -c "from app.api.v1.recommendation_engine import get_weights_for_group; print(get_weights_for_group('test_a'))"

# 이벤트 스키마에 not_interested 포함 확인
python -c "from app.schemas.user_event import EventCreate; e = EventCreate(event_type='not_interested', movie_id=1); print('OK')"

# 앱 시작 확인
python -c "from app.main import app; print('app OK')"

# Ruff 린트
ruff check backend/app/models/user.py backend/app/api/v1/recommendations.py backend/app/api/v1/events.py
```

---

결과를 claude_results.md에 **기존 내용 아래에 --- 구분선 후 이어서** 저장:

```markdown
---

# Phase 4-1: A/B 테스트 프레임워크 + 추천 품질 대시보드 결과

## 날짜
YYYY-MM-DD

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/app/models/user.py | experiment_group 컬럼 추가 |
| backend/app/api/v1/auth.py | 회원가입 시 랜덤 그룹 배정 |
| backend/app/api/v1/recommendation_engine.py | get_weights_for_group 함수 추가 |
| backend/app/api/v1/recommendation_constants.py | WEIGHTS_HYBRID_A/B 추가 |
| backend/app/api/v1/recommendations.py | experiment_group 분기 적용 |
| backend/app/api/v1/events.py | AB report 엔드포인트 + not_interested 이벤트 |
| backend/app/schemas/user_event.py | not_interested 이벤트 타입 추가 |

## 실험 그룹
| 그룹 | 알고리즘 | CF 비중 |
|------|---------|--------|
| control | Rule-based only | 0% |
| test_a | Hybrid | 50% |
| test_b | Hybrid | 70% |

## API 엔드포인트
| 메서드 | 경로 | 용도 |
|--------|------|------|
| GET | /api/v1/events/ab-report | A/B 테스트 리포트 |

## 검증 결과
- experiment_group: 모델 OK ✅
- 가중치 분기: OK ✅
- not_interested 이벤트: OK ✅
- Ruff: No errors ✅
```

git add -A && git commit -m 'feat: A/B 테스트 프레임워크 (실험 그룹 분기 + 추천 품질 리포트 + 관심없음 이벤트)' && git push origin HEAD:main