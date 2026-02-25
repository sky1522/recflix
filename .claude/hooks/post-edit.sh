#!/bin/bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"//')
if [ -z "$FILE" ]; then exit 0; fi

echo '✅ 편집 체크:'
echo '  □ any 타입 사용 금지'
echo '  □ console.log 제거'

case "$FILE" in
  backend/app/api/v1/*) echo '  □ ruff check 통과 확인' ;;
  backend/app/models/*) echo '  □ Alembic revision 필요?' ;;
  frontend/components/*) echo '  □ 모바일 뷰 확인 (360px)' ;;
  frontend/app/*) echo '  □ npm run build 확인' ;;
esac
