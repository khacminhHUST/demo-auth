#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
TAG="${1:-}"

if [ -z "$TAG" ]; then
    echo "Dùng: ./rollback.sh <tag>"
    docker images demo-auth_be --format '  {{.Tag}}\t(tạo {{.CreatedSince}})' || true
    tail -n 10 shared/releases.log 2>/dev/null || true
    exit 1
fi

# GUARD: image tag này PHẢI tồn tại — nếu không, dừng (tránh `up` build lại code
# HIỆN TẠI rồi gắn nhầm tag cũ).
if ! docker image inspect "demo-auth_be:$TAG" >/dev/null 2>&1 \
   || ! docker image inspect "demo-auth_fe:$TAG" >/dev/null 2>&1; then
    echo "LỖI: không có image demo-auth_be:$TAG / demo-auth_fe:$TAG trên server."
    exit 1
fi

./scripts-deploy/write-override.sh "$TAG"
docker compose up -d --no-build                 # thay ruột từ cache, KHÔNG build
mkdir -p shared
printf '%s  %s  ROLLBACK\n' "$(date -Iseconds)" "$TAG" >> shared/releases.log
echo "$TAG" > shared/CURRENT_TAG
docker compose ps
