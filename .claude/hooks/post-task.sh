#!/bin/bash
echo ''
echo '🔍 RecFlix 자동 품질 검사'
echo '═══════════════════'

CHANGED=$(git diff --name-only 2>/dev/null)
if [ -n "$CHANGED" ]; then
  echo "📝 미커밋 변경: $(echo "$CHANGED" | wc -l)개 파일"
fi

# Backend 변경 감지
BE_CHANGED=$(echo "$CHANGED" | grep '^backend/')
if [ -n "$BE_CHANGED" ]; then
  echo ''
  echo '🐍 Backend 변경 감지:'
  cd backend 2>/dev/null && python -m ruff check app/ --statistics 2>&1 | tail -5
  echo '  □ pytest 통과 확인'
fi

# Frontend 변경 감지
FE_CHANGED=$(echo "$CHANGED" | grep '^frontend/')
if [ -n "$FE_CHANGED" ]; then
  echo ''
  echo '⚛️ Frontend 변경 감지:'
  ANY_COUNT=$(echo "$CHANGED" | xargs grep -l ': any\|as any' 2>/dev/null | wc -l)
  if [ "$ANY_COUNT" -gt 0 ]; then
    echo "  ⚠️ any 타입 발견: $ANY_COUNT개 파일"
  fi
  echo '  □ tsc --noEmit 통과 확인'
  echo '  □ npm run build 통과 확인'
fi

# DB 변경 감지
DB_CHANGED=$(echo "$CHANGED" | grep -E 'models/|alembic/')
if [ -n "$DB_CHANGED" ]; then
  echo ''
  echo '🚨 DB 스키마 변경 감지! Alembic revision 필요'
fi

# 추천 로직 변경 감지
REC_CHANGED=$(echo "$CHANGED" | grep 'recommendation')
if [ -n "$REC_CHANGED" ]; then
  echo ''
  echo '🧠 추천 로직 변경! A/B 그룹별 영향 확인 필요'
fi

BRANCH=$(git branch --show-current 2>/dev/null)
echo ''
echo "📋 커밋 전 체크: 브랜치=$BRANCH"
echo '  □ backend: ruff + pytest'
echo '  □ frontend: tsc + build + lint'
echo '  □ 문서 업데이트 필요?'
