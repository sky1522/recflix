## 리뷰 대상: Step 05A — 다중 모델 비교 + Interleaving

### 리뷰 범위
- backend/scripts/compare_models.py (신규)
- backend/scripts/run_interleaving.py (신규)
- backend/app/services/interleaving.py (신규)

### 체크리스트

#### compare_models.py
- [ ] 5개 모델 랭킹 생성 (Popularity, MBTI, Hybrid, TwoTower only, TwoTower+LGBM)
- [ ] LGBM 모델 없으면 해당 모델 스킵하고 나머지만 비교
- [ ] NDCG/Recall/MRR/HitRate × K=5,10,20 계산
- [ ] Coverage, Novelty 다양성 지표 포함
- [ ] Bootstrap CI 계산
- [ ] Ablation Study 표 생성 (단계별 누적 개선)
- [ ] Markdown + JSON 출력
- [ ] DB 조회 없음 (JSONL + 모델 파일만 사용)

#### interleaving.py
- [ ] team_draft_interleave: 팀 크기 균형 유지하며 교대 선택
- [ ] 중복 movie_id 방지 (seen set)
- [ ] compute_interleaving_result: clicked_ids ∩ team_a/b 비교
- [ ] compute_win_rate: 승률 + 95% CI (binomial)

#### run_interleaving.py
- [ ] test.jsonl에서 request별 두 모델 랭킹 생성
- [ ] team_draft_interleave로 섞기
- [ ] label > 0을 "클릭"으로 간주
- [ ] 승률 + CI 출력
- [ ] JSON 결과 저장

#### 안전성
- [ ] scipy 미사용
- [ ] 기존 코드 수정 없음
- [ ] 빈 데이터 처리

### 발견사항 분류
- CRITICAL: 지표 오류, 데이터 누수
- WARNING: 모델 누락, CI 오류
- INFO: 포맷팅

### 출력
결과를 codex_results.md에 저장하세요.