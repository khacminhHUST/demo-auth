#!/usr/bin/env bash
# Tự kiểm repo trước khi deploy/CI, theo đúng tiêu chí HUONG_DAN_CHUAN_BI_REPO.md mục 8.
# Exit 0 = PASS, exit 1 = còn FAIL.
set -uo pipefail

ROOT="${1:-.}"
cd "$ROOT" || { echo "Không vào được thư mục: $ROOT"; exit 1; }

fail=0
warn() { echo "WARN: $1"; }
error() { echo "FAIL: $1"; fail=1; }
ok() { echo "OK:   $1"; }

echo "== check_repo.sh — kiểm tra tại $(pwd) =="

# 1. .gitignore ở gốc
if [ -f ".gitignore" ]; then
  ok ".gitignore tồn tại"
else
  error "Thiếu .gitignore ở gốc dự án"
fi

# 2 + 3. .env bị loại trừ & không bị track
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ -f ".env" ] && ! git check-ignore -q ".env"; then
    error ".env tồn tại nhưng KHÔNG bị .gitignore loại trừ"
  else
    ok ".env bị loại trừ (hoặc không tồn tại)"
  fi

  tracked_env=$(git ls-files | grep -E '(^|/)\.env(\..+)?$' | grep -v '\.env\.example$' || true)
  if [ -n "$tracked_env" ]; then
    error "Có file .env bị commit vào git:"
    echo "$tracked_env" | sed 's/^/      /'
  else
    ok "Không có file .env nào bị track (ngoài .env.example)"
  fi

  # 4. .env.example tồn tại
  example_count=$(git ls-files | grep -c '\.env\.example$' || true)
  if [ "$example_count" -gt 0 ]; then
    ok ".env.example có trong git ($example_count file)"
  else
    warn "Không thấy .env.example nào được track"
  fi

  # 5. private key / cert không bị commit
  leaked=$(git ls-files | grep -E '(server\.key|.*private.*\.pem|id_rsa|\.p12$|\.pfx$)' || true)
  if [ -n "$leaked" ]; then
    error "Có private key/cert bị commit:"
    echo "$leaked" | sed 's/^/      /'
  else
    ok "Không có private key/cert nào bị commit"
  fi
else
  warn "Chưa phải git repo (git init chưa chạy) — bỏ qua các kiểm tra liên quan tới git"
fi

# 6. Python — mọi dòng requirements*.txt phải pin == (hoặc @)
py_files=$(find . -maxdepth 3 -name "requirements*.txt" -not -path "*/node_modules/*" 2>/dev/null)
if [ -n "$py_files" ]; then
  py_bad=0
  for f in $py_files; do
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      case "$line" in
        \#*) continue ;;
        -r\ *) continue ;;
      esac
      if ! echo "$line" | grep -qE '(==|@)'; then
        error "Dòng chưa pin version trong $f: $line"
        py_bad=1
      fi
    done < "$f"
  done
  [ "$py_bad" = 0 ] && ok "Mọi dòng requirements*.txt đã pin version"
fi

# 7. Node — package.json thì phải đúng 1 lockfile
node_files=$(find . -maxdepth 3 -name "package.json" -not -path "*/node_modules/*" 2>/dev/null)
for pkg in $node_files; do
  dir=$(dirname "$pkg")
  lockfiles=$(find "$dir" -maxdepth 1 \( -name "package-lock.json" -o -name "pnpm-lock.yaml" -o -name "yarn.lock" \) 2>/dev/null | wc -l)
  if [ "$lockfiles" -eq 1 ]; then
    ok "Đúng 1 lockfile Node tại $dir"
  elif [ "$lockfiles" -eq 0 ]; then
    error "Thiếu lockfile Node tại $dir (chạy npm install để sinh package-lock.json)"
  else
    error "Có nhiều hơn 1 lockfile Node tại $dir — chỉ được dùng 1 package manager"
  fi
done

# 8. Docker — mọi FROM phải có tag cụ thể, không :latest, không tag trần
dockerfiles=$(find . -maxdepth 3 -iname "Dockerfile*" -not -path "*/node_modules/*" 2>/dev/null)
for df in $dockerfiles; do
  while IFS= read -r line; do
    image=$(echo "$line" | awk '{print $2}')
    [ -z "$image" ] && continue
    if [[ "$image" != *:* ]]; then
      error "$df: FROM không có tag (\"$image\") — image trần = có thể đổi dưới chân"
    elif [[ "$image" == *:latest ]]; then
      error "$df: FROM dùng tag :latest (\"$image\") — phải pin bản cụ thể"
    else
      ok "$df: FROM $image (đã pin tag)"
    fi
  done < <(grep -iE '^\s*FROM\s' "$df")
done

echo "=============================="
if [ "$fail" -eq 0 ]; then
  echo "PASS — repo sẵn sàng."
  exit 0
else
  echo "FAIL — sửa các mục trên rồi chạy lại."
  exit 1
fi
