#!/usr/bin/env bash
set -e

FILE="pyproject.toml"
VERSION="$1"

if [ ! -f "$FILE" ]; then
  echo "Error: $FILE not found in current directory."
  exit 1
fi

# 备份
cp "$FILE" "${FILE}.bak"
echo "[INFO] Backup saved to ${FILE}.bak"

# 1️⃣ 在 [project] 中：只有当还不存在 version 时，才在 name="vllm" 后插入 version
if awk '
  /^\[project\]/{in_project=1; next}
  in_project && /^\[/{exit}
  in_project && index($0, "version = \"0.0.0\"") {found=1; exit}
  END { exit(found?0:1) }
' "$FILE"; then
  echo "[INFO] version already exists, skip inserting."
else
  echo "[INFO] inserting version..."

  awk -v version="$VERSION" '
  BEGIN { in_project=0; inserted=0 }
  /^\[project\]/ { in_project=1 }
  in_project && /^\[/ && $0 !~ /^\[project\]/ { in_project=0 }

  {
    print
    if (in_project && !inserted && index($0, "name = \"vllm\"")) {
      print "version = \"" version "\""
      inserted=1
    }
  }
  ' "$FILE" > tmp_pyproject.toml

  mv tmp_pyproject.toml "$FILE"
fi

# 2️⃣ 删除 dynamic 中的 "version"
sed -i -E '
s/"version",[[:space:]]*//g;
s/[[:space:]]*"version"//g;
s/\[[[:space:]]*,/\[/g;
s/,[[:space:]]*\]/\]/g
' "$FILE"

echo "[INFO] pyproject.toml updated successfully."