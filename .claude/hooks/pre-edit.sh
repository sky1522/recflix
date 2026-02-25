#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"//')
if [ -z "$FILE" ]; then exit 0; fi

case "$FILE" in
  backend/app/api/v1/recommendation*)
    echo '🧠 [추천] .claude/skills/recommendation.md 확인'
    echo '  • 가중치 변경 시 A/B 그룹별 영향 확인'
    echo '  • 다양성 후처리 파이프라인 순서 유지'
    ;;
  backend/app/api/v1/*)
    echo '🔌 [API] .claude/skills/api.md 확인'
    echo '  • 에러 응답 형식 통일, rate limit 확인'
    ;;
  backend/app/models/*)
    echo '🗄️ [DB] .claude/skills/database.md 확인'
    echo '  • Alembic 마이그레이션 필요 여부 확인'
    ;;
  backend/app/core/security*)
    echo '🔒 [보안] JWT/Redis 토큰 로직 주의'
    ;;
  backend/app/services/*)
    echo '⚙️ [서비스] 외부 API 호출 시 에러 핸들링 확인'
    ;;
  backend/tests/*)
    echo '🧪 [테스트] conftest.py의 SQLite 제약 확인'
    ;;
  frontend/app/page.tsx)
    echo '🏠 [홈] 캐시 키 구조, 추천 섹션 순서 주의'
    ;;
  frontend/components/movie/*)
    echo '🎬 [영화 UI] .claude/skills/frontend-patterns.md 확인'
    echo '  • 모바일 터치 영역 44px 준수'
    ;;
  frontend/components/search/*)
    echo '🔍 [검색] ARIA combobox 패턴 유지'
    ;;
  frontend/stores/*)
    echo '📦 [상태] Zustand 패턴 유지, localStorage 키 충돌 주의'
    ;;
  frontend/lib/api.ts)
    echo '🌐 [API 클라이언트] fetchAPI 시그니처 하위 호환 유지'
    ;;
esac
