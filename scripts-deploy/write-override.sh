#!/usr/bin/env bash
set -euo pipefail
TAG="${1:?Dùng: write-override.sh <tag> [dir]}"
DIR="${2:-.}"
cat > "$DIR/docker-compose.override.yml" <<EOF
# TỰ SINH — đừng sửa tay. Con trỏ phiên bản đang chạy.
services:
  be: { image: demo-auth_be:$TAG }
  fe: { image: demo-auth_fe:$TAG }
EOF
