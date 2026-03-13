# 맞춤 추천(hybrid_row) 품질 긴급 수정 — 시연 전 조치

## 배경
Codex 조사 결과, hybrid_row 품질 문제는 test_a/test_b A/B 그룹에서 발생합니다.
- control: 날씨/기분/MBTI 변경 시 top10 overlap 1/10 (정상 반응)
- test_a: top10 overlap 9/10 (거의 변화 없음)
- test_b: top10 overlap 9/10 (거의 변화 없음)

원인:
1. Two-Tower 후보 추출이 weather/mood를 사용하지 않아 후보 200편이 고정
2. LightGBM reranker의 mood vocabulary가 프론트와 불일치
   (reranker: happy/sad/excited/calm/tired/emotional)
   (프론트: relaxed/tense/excited/emotional/imaginative/light/gloomy/stifled)
   → 8개 중 2개만 인식, 나머지 6개는 전부 0 처리
3. test_b는 CF 70%로 다른 축의 영향이 극히 미미

## 수정 1: hybrid_row를 control 로직으로 강제 (최우선)

### 파일: backend/app/api/v1/recommendations.py

hybrid_row 생성 부분에서 A/B 그룹 분기를 무시하고 control 로직만 사용하도록 수정.

현재 흐름:
- experiment_group 판정 → control/test_a/test_b 분기 → 각각 다른 hybrid 계산

수정 방향:
- hybrid_row 계산 시 experiment_group에 관계없이 항상 control 경로 사용
- 즉, DB 전체 스캔 → 5축 가중합산(MBTI 20% + Weather 15% + Mood 25% + Personal 15% + CF 25%) → Top 20
- Two-Tower/LightGBM 경로를 hybrid_row에서 비활성화
- 개별 섹션(weather_row, mood_row, mbti_row)은 기존 로직 유지

구체적으로:
- hybrid_row를 계산하는 함수 호출 부분을 찾아서
- test_a/test_b 분기를 주석 처리하거나
- force_control=True 같은 플래그로 항상 control 경로를 타도록

### 주의사항
- A/B 테스트 인프라 자체는 건드리지 않음 (나중에 복원 가능)
- 개별 추천 섹션(weather_row, mood_row 등)은 이미 control 로직이므로 영향 없음
- 추천 로그에 기록되는 experiment_group은 그대로 유지 (분석용)

## 수정 2: mood vocabulary 매핑 추가 (시간 되면)

### 파일: backend/app/services/reranker.py:36-37

현재 MOOD_TO_IDX:
```python
MOOD_TO_IDX = {"happy": 0, "sad": 1, "excited": 2, "calm": 3, "tired": 4, "emotional": 5}
```

프론트 mood enum과의 매핑 추가:
```python
MOOD_MAPPING = {
    "relaxed": "calm",
    "tense": "excited",     # 가장 가까운 매칭
    "excited": "excited",
    "emotional": "emotional",
    "imaginative": "happy",
    "light": "happy",
    "gloomy": "sad",
    "stifled": "tired",
}
```

reranker.py에서 mood feature 생성 전에 이 매핑을 적용.
이 수정은 수정 1과 독립적이므로, 나중에 test_a를 다시 활성화할 때를 위해 함께 수정.

## 수정 3: 로그인 사용자 MBTI 쿼리 override 허용 (선택)

### 파일: backend/app/api/v1/recommendations.py:121-123

현재:
```python
mbti = current_user.mbti if current_user else mbti
```

수정 (헤더 MBTI 드롭다운 변경이 로그인 상태에서도 hybrid_row에 반영되도록):
```python
mbti = mbti or (current_user.mbti if current_user else None)
```

쿼리 파라미터가 있으면 우선, 없으면 user DB 값 사용.

## 검증

수정 후 아래 시나리오 확인:
1. 로그인 상태에서 날씨 맑음→비 변경 → hybrid_row 영화 목록 변경 확인
2. 기분 편안한→긴장감 변경 → hybrid_row 영화 목록 변경 확인
3. MBTI INTJ→ENFP 변경 → hybrid_row 영화 목록 변경 확인
4. hybrid_row 영화가 조건과 어울리는지 체감 확인
   (비+긴장감+INTJ → 다크나이트, 기생충 등 기대)
5. 비로그인 상태에서는 hybrid_row가 표시되지 않는지 확인
6. % 표시가 65~99% 범위인지 확인

## 완료 후
- 커밋: "fix: force control algorithm for hybrid_row to ensure context responsiveness"
- push 및 배포 확인
- 시연 시나리오 전체 재점검
- 결과를 claude_results.md에 기록