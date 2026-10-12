#!/usr/bin/bash
# 서버를 내리고, servers 폴더를 새로 생성한 뒤 다시 올린다.
# 사용법: ./redeploy.sh            # 모든 서버
#         ./redeploy.sh server1    # server1 만 (down/삭제/sync/up 모두)

set -euo pipefail
cd "$(dirname "$0")"

# 서버를 내리기 전에 인자부터 검사한다 (../ 같은 경로로 엉뚱한 폴더를 지우지 않도록)
for name in "$@"; do
    if [[ -z "$name" || "$name" == *"/"* || "$name" == "." || "$name" == ".." ]]; then
        echo "잘못된 서버 이름: '$name'" >&2
        exit 1
    fi
done

echo "==> docker compose down $*"
docker compose down "$@"

if [ $# -eq 0 ]; then
    echo "==> rm -rf servers"
    rm -rf ./servers
else
    for name in "$@"; do
        echo "==> rm -rf servers/$name"
        rm -rf "./servers/$name"
    done
fi

echo "==> ./sync.sh $*"
./sync.sh "$@"

echo "==> docker compose up -d $*"
docker compose up -d "$@"
