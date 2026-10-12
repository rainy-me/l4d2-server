#!/usr/bin/bash
# 서버를 내리고, servers/<서버>/ 폴더를 새로 생성한 뒤 다시 올린다.
# 로그, DB 까지 모두 지운다. 남기려면 ./sync.sh --restart 를 쓸 것.
# 빌드(git pull, 플러그인 컴파일)가 끝난 뒤에 서버를 하나씩 내리므로, 빌드가 실패하면 서버는 그대로 돌아간다.
# 사용법: ./redeploy.sh            # 모든 서버
#         ./redeploy.sh server1    # server1 만

set -euo pipefail
cd "$(dirname "$0")"

exec ./sync.sh --recreate "$@"
