# Step 02C: Synthetic 상호작용 데이터 생성

> 작업일: 2026-02-27
> 목적: Two-Tower 사전학습용 가상 데이터 생성 + Step 01~02 파이프라인 검증

## 생성 파일

| 파일 | 설명 |
|------|------|
| `backend/scripts/generate_synthetic_data.py` | Synthetic 데이터 생성 CLI (437줄) |
| `data/synthetic/train.jsonl` | 학습셋 (42,280 records, 28.7MB) |
| `data/synthetic/valid.jsonl` | 검증셋 (9,060 records, 6.1MB) |
| `data/synthetic/test.jsonl` | 테스트셋 (9,060 records, 6.1MB) |
| `data/synthetic/stats.json` | 통계 요약 |
| `data/synthetic/reports/eval_*.json` | 오프라인 평가 리포트 3종 |

## CLI 사용 예시

```bash
python backend/scripts/generate_synthetic_data.py \
  --db-url "$DATABASE_URL" \
  --n-users 500 \
  --sessions-per-user 2 \
  --candidates-per-session 80 \
  --output-dir data/synthetic/ \
  --seed 42 --verbose
```

## 통계 리포트

```
Users: 500 synthetic
Sessions: 755
Total impressions: 60,400
Label distribution:
  0 (negative)                45,135 (74.7%)
  1 (weak positive)            6,256 (10.4%)
  2 (positive)                 5,082 (8.4%)
  3 (strong positive)          3,927 (6.5%)
Positive rate (label>0): 25.3%
Genre coverage: 19/19 genres
Movie coverage: 25,265/42,917 (58.9%)
Split:
  Train:  42,280 (70.0%)
  Valid:   9,060 (15.0%)
  Test:    9,060 (15.0%)
```

## offline_eval.py 호환성 테스트

```
Comparison vs Current Model (NDCG@10)
┌──────────────────────────────────────────────────┐
│ Model            NDCG@10         Δ        Δ%     │
├──────────────────────────────────────────────────┤
│ Popularity         0.233    -0.053    -18.5%     │
│ MBTI-only          0.284    -0.002     -0.6%     │
│ Current (hybrid)   0.286         -         -     │
└──────────────────────────────────────────────────┘
```

Current(hybrid) > MBTI-only > Popularity 순서 확인 — 파이프라인 정상 동작.

## 검증 결과

| 항목 | 결과 |
|------|------|
| train.jsonl + valid.jsonl + test.jsonl 생성 | OK |
| 출력 JSONL이 Step 02A 포맷과 완전 호환 | OK |
| offline_eval.py로 평가 가능 (에러 없이 리포트 생성) | OK |
| negative 60~80% (74.7%) | OK |
| positive 20~40% (25.3%) | OK |
| Genre coverage 19/19 | OK |
| MBTI 16종 균등 분포 | OK |
| Movie coverage 58.9% (25,265/42,917) | OK |
| --seed 42 동일 → 동일 출력 (재현성) | OK |
| stats.json 생성 | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |

## 재현성 보장 수정사항

- DB 쿼리에 `ORDER BY m.id` 추가 (movies 로드 순서 결정론적)
- `uuid.uuid4()` → `uuid.UUID(int=random.getrandbits(128))` (시드 기반 결정론적 UUID)
