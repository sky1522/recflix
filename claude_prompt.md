claude "/sync-docs Phase 52 A/B 테스트 강화

Phase 52A: 이벤트 사각지대 해소 + 추천 컨텍스트 전파 + preferred_genres 가중치 3배
Phase 52B: A/B 리포트 통계 유의성(Z-test) + 추가 메트릭 + 그룹 비율 조절

신규 파일: backend/app/api/v1/ab_stats.py
변경 파일: events.py, auth.py, config.py, schemas/user_event.py, recommendation_engine.py, MovieModal.tsx, FeaturedBanner.tsx, MovieCard.tsx, HybridMovieCard.tsx, movies/[id]/page.tsx

업데이트 대상:
- CLAUDE.md (신규 파일, 설정 추가)
- CHANGELOG.md (Phase 52 항목)
- PROGRESS.md (Phase 52 완료)
- docs/HANDOFF_CONTEXT.md (A/B 현황 업데이트)
- docs/RECOMMENDATION_LOGIC.md (이벤트 트래킹, A/B 메트릭)
- docs/DECISION.md (통계 검증 방식 결정, 그룹 비율 조절 결정)
- .claude/skills/recommendation.md (A/B 가중치, 이벤트)
- .claude/skills/frontend-patterns.md (이벤트 트래킹 패턴)

git tag v1.1.0 -m 'RecFlix v1.1.0 — A/B 테스트 고도화'"