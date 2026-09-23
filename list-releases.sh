#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "== Bản đang chạy =="
if [ -f "shared/CURRENT_TAG" ]; then
  echo "  $(cat shared/CURRENT_TAG)"
else
  echo "  (chưa rõ — chưa từng deploy qua CI/CD?)"
fi

echo
echo "== Các tag image có sẵn trên server (rollback được) =="
docker images demo-auth_be --format '  {{.Tag}}\t(tạo {{.CreatedSince}})' || true

echo
echo "== Lịch sử deploy/rollback (10 dòng gần nhất) =="
tail -n 10 shared/releases.log 2>/dev/null || echo "  (chưa có shared/releases.log)"
