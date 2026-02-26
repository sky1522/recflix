## 작업: 실험 그룹 결정론적 배정 + algorithm_version 레지스트리

### 배경
현재 experiment_group은 _weighted_random_group()으로 매 요청마다 랜덤 배정됩니다.
A/B 비교를 위해서는 같은 사용자/세션이 항상 같은 그룹에 배정되어야 합니다.
또한 algorithm_version을 체계적으로 관리하여, 향후 Two-Tower 등 새 알고리즘 추가 시
GROUP_ALGORITHM_MAP 한 줄만 바꾸면 실험이 가능한 구조를 만듭니다.

### 요구사항

#### 1. 결정론적 그룹 배정 함수

backend/app/api/v1/recommendations.py (또는 적절한 위치)에 추가:
```python
import hashlib

def get_deterministic_group(
    user_id: Optional[int],
    session_id: Optional[str],
    weights: dict[str, int]  # {"control": 34, "test_a": 33, "test_b": 33}
) -> str:
    """
    동일 사용자/세션은 항상 같은 그룹을 반환.
    
    로직:
    1. seed = str(user_id) if user_id else (session_id or "anonymous")
    2. bucket = md5(seed) % 100
    3. weights 순서대로 누적하여 bucket이 속하는 그룹 반환
    """
    seed = str(user_id) if user_id else (session_id or "anonymous")
    hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    bucket = hash_val % 100
    
    cumulative = 0
    for group, weight in weights.items():
        cumulative += weight
        if bucket < cumulative:
            return group
    return list(weights.keys())[-1]  # fallback
```

기존 _weighted_random_group() 호출부를 이 함수로 교체합니다.
단, 기존 함수는 삭제하지 않고 주석 처리 또는 유지 (rollback 가능하도록).

#### 2. algorithm_version 레지스트리

backend/app/api/v1/recommendation_constants.py에 추가:
```python
# 실험 그룹별 알고리즘 버전 매핑
# 새 알고리즘 도입 시 이 딕셔너리만 수정하면 됨
GROUP_ALGORITHM_MAP: dict[str, str] = {
    "control": "hybrid_v1",
    "test_a": "hybrid_v1_test_a",
    "test_b": "hybrid_v1_test_b",
}

def get_algorithm_version(experiment_group: str) -> str:
    """실험 그룹에 해당하는 알고리즘 버전을 반환"""
    return GROUP_ALGORITHM_MAP.get(experiment_group, "hybrid_v1")
```

#### 3. recommendations.py에서 활용

get_home_recommendations()에서:
- 기존 랜덤 배정을 결정론적 배정으로 교체
- algorithm_version을 레지스트리에서 가져오기
```python
# 변경 전
experiment_group = _weighted_random_group()
algorithm_version = f"hybrid_v1_{experiment_group}"

# 변경 후
from backend.app.api.v1.recommendation_constants import get_algorithm_version

session_id = request.headers.get("X-Session-ID")
experiment_group = get_deterministic_group(
    user_id=current_user.id if current_user else None,
    session_id=session_id,
    weights=get_experiment_weights()  # 기존 환경변수 체계 재사용
)
algorithm_version = get_algorithm_version(experiment_group)
```

#### 4. 프론트엔드 session_id 생성 + 전송

frontend/lib/api.ts 또는 적절한 위치:
- 앱 최초 로드 시 localStorage에 session_id가 없으면 생성 (crypto.randomUUID() 또는 uuid)
- 모든 API 호출의 헤더에 X-Session-ID 포함
```typescript
function getSessionId(): string {
    const KEY = 'recflix_session_id';
    let sid = localStorage.getItem(KEY);
    if (!sid) {
        sid = crypto.randomUUID();
        localStorage.setItem(KEY, sid);
    }
    return sid;
}

// fetchAPI 또는 axios 인터셉터에서:
headers['X-Session-ID'] = getSessionId();
```

주의: localStorage가 비어있는 경우(첫 방문) 자동 생성되므로 에러 없음.

#### 5. 기존 환경변수 체계 유지

EXPERIMENT_WEIGHTS 환경변수는 그대로 유지합니다.
get_experiment_weights()가 반환하는 딕셔너리를 get_deterministic_group의 weights 인자로 사용합니다.

### 검증
1. 같은 user_id로 추천 API 5회 호출 → 항상 같은 experiment_group 반환
2. 다른 user_id 10개로 호출 → weights 비율에 근사하게 분배
3. 비로그인 + 같은 session_id → 항상 같은 그룹
4. reco_impressions에 algorithm_version이 GROUP_ALGORITHM_MAP 값과 일치
5. 프론트엔드에서 X-Session-ID 헤더가 전송되는지 확인
6. 기존 pytest 통과
7. 프론트엔드 빌드 성공

### 금지사항
- 기존 EXPERIMENT_WEIGHTS 환경변수 삭제 금지
- 기존 가중치 계산 로직(get_weights_for_group 등) 삭제 금지
- GROUP_ALGORITHM_MAP을 환경변수가 아닌 코드 상수로 유지 (빈번한 변경 불필요, 배포 단위로 관리)

### 완료 후
작업 결과를 claude_results.md에 저장하세요. 포함 내용:
- 생성/수정 파일 목록
- 결정론적 배정 로직 설명
- 검증 결과 (그룹 일관성 테스트)
- GROUP_ALGORITHM_MAP 현재 값