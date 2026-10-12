#!/usr/bin/bash
# 사용법: ./sync.sh            # 모든 서버
#         ./sync.sh server1    # server1 만

set -euo pipefail
cd "$(dirname "$0")"

for repo in ../l4d2-sourcemod ../l4d2-settings; do
    echo "==> git pull -r: $repo"
    git -C "$repo" pull -r
done

uv run sync.py "$@"
