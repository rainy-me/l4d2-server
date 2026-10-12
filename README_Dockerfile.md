# Left 4 Dead 2 Dedicated Server Docker Image

이 저장소의 `Dockerfile`은 SteamCMD로 바닐라 L4D2 데디케이티드 서버를 설치한 Docker 이미지를 만듭니다.  
설정은 환경 변수로 넘기고, `entrypoint.sh`가 이를 `srcds_run` 실행 인자로 바꿔줍니다.

## 이미지 빌드

```shell
docker build -t l4d2 .
# 캐시 없이 처음부터 다시 빌드
docker build --pull --no-cache -t l4d2 .
```

## 시작하기

기본 설정으로 서버 한 대를 띄우는 가장 단순한 형태입니다.

```shell
docker run -it --init --name l4d2 \
    --network host \
l4d2
```

> [!IMPORTANT]
> 호스트 네트워킹(`--network host`)을 권장합니다.  
> 게임 서버가 접속자의 실제 IP를 알 수 있습니다.

### 브리지 네트워킹

이 경우 서버는 모든 접속자를 같은 IP(게이트웨이)로 인식합니다.  
게임 포트를 TCP, UDP 모두 공개하세요.  
RCON을 사용하지 않는다면 UDP만 공개하세요.

```shell
docker run -it --init --name l4d2-bridged \
    -p 27015:27015/tcp \
    -p 27015:27015/udp \
l4d2
```

> [!WARNING]
> 브리지 네트워킹에서 포트를 공개할 때는 호스트 포트와 컨테이너 포트를 같은 번호로 맞추세요.  
> 다르면 매치메이킹에 잘못된 포트가 광고되어 새 플레이어가 접속하지 못합니다.

### 재시작 동작

`srcds_run`에는 서버 프로세스가 죽으면 다시 띄우는 워치독이 들어 있습니다.
호스트 재부팅 뒤에도 서버가 올라오게 하려면 `--restart`를 붙이세요.

```shell
docker run -it --init --name l4d2-reboot \
    --restart unless-stopped \
l4d2
```

## 서버 콘솔과 로그

`docker run -it`로 띄웠다면 서버 콘솔에 직접 붙을 수 있습니다.

```shell
docker attach l4d2
```

콘솔에서 나올 때는 `Ctrl+P`, `Ctrl+Q`를 누르세요. `Ctrl+C`는 서버를 종료합니다.  
로그만 보려면:

```shell
docker logs -f l4d2
```

## 게임 접속 방법

- 로비를 만들고 서버 유형을 **최적의 전용 서버(Best Available Dedicated)** 로 둔 뒤, 개발자 콘솔에서
  `mm_dedicated_force_servers [ip:port]`를 입력하면 게임 시작 시 이 서버를 우선 사용합니다.
- `STEAM_GROUP`을 설정하면 로비에서 Steam 그룹 서버로 시작할 수 있습니다.
- 게임 내 서버 브라우저(`openserverbrowser`)에서 즐겨찾기에 추가하면 메뉴에 Steam 그룹 서버처럼 표시됩니다.
- 개발자 콘솔에서 `connect [ip:port]`로 직접 접속할 수 있습니다.
- Steam 클라이언트 **보기 > 게임 서버** 메뉴에서도 열 수 있습니다.
- 같은 LAN의 서버는 자동으로 Steam 그룹 서버 목록에 나타납니다.

## 애드온과 설정 파일

- 애드온 파일(.vpk)과 SourceMod는 `/home/ubuntu/l4d2/left4dead2/addons`에 마운트하세요.
- 설정 파일(.cfg)은 `/home/ubuntu/l4d2/left4dead2/cfg/`에 마운트하세요.
- `cfg/` 전체를 마운트하면 게임 기본 cfg 파일이 사라지므로, 파일이나 하위 폴더 단위로 마운트하세요.
- MOTD는 `/home/ubuntu/l4d2/left4dead2/host.txt`, `/home/ubuntu/l4d2/left4dead2/motd.txt`에 마운트하세요.

```shell
docker run -it --init --name l4d2-addons \
    -v $(pwd)/addons:/home/ubuntu/l4d2/left4dead2/addons \
    -v $(pwd)/cfg/sourcemod:/home/ubuntu/l4d2/left4dead2/cfg/sourcemod \
    -v $(pwd)/cfg/server.cfg:/home/ubuntu/l4d2/left4dead2/cfg/server.cfg \
    -v $(pwd)/host.txt:/home/ubuntu/l4d2/left4dead2/host.txt \
    -v $(pwd)/motd.txt:/home/ubuntu/l4d2/left4dead2/motd.txt \
l4d2
```

## 설정

### 환경 변수

| 변수                    | 기본값       | 설명                                           |
| ----------------------- | ------------ | ---------------------------------------------- |
| `HOSTNAME`              | (빈 값)      | 서버 브라우저에 표시되는 서버 이름             |
| `PORT`                  | `27015`      | 게임 포트                                      |
| `STEAM_GROUP`           | `0`          | 연결할 Steam 그룹 ID. `0`이면 사용 안 함       |
| `STEAM_GROUP_EXCLUSIVE` | `0`          | `1`이면 그룹 멤버만 로비 리더로 서버 선택 가능 |
| `DEFAULT_MAP`           | `c1m1_hotel` | 서버 시작 시 첫 맵                             |
| `DEFAULT_MODE`          | `coop`       | 서버 시작 시 게임 모드                         |
| `GAME_TYPES`            | (빈 값)      | 허용할 게임 모드 목록. 비우면 전부 허용        |
| `MOTD`                  | `0`          | 접속 시 MOTD 자동 표시 (`1`/`0`)               |
| `EXTRA_ARGS`            | (빈 값)      | `srcds_run`에 그대로 덧붙일 추가 인자          |

#### STEAM_GROUP

Steam 그룹에 서버를 연결하면 접속이 쉬워집니다.  
그룹 서버는 게임 메뉴 오른쪽 아래에 표시되고, 로비에서 호스팅 옵션으로 바로 고를 수 있습니다.  
그룹 ID는 그룹 관리 페이지 상단에서 확인할 수 있습니다.

#### STEAM_GROUP_EXCLUSIVE

기본적으로 서버는 **최적의 전용 서버** 설정을 쓰는 누구에게나 배정될 수 있습니다.  
`STEAM_GROUP_EXCLUSIVE=1`로 두면 그룹 멤버가 로비 리더일 때만 배정됩니다.

> [!NOTE]
> 그룹 멤버가 아니어도 `mm_dedicated_force_servers`로는 여전히 접속할 수 있습니다.

### server.cfg

서버는 시작 시 `server.cfg`를 읽습니다.  
설정이 많다면 파일로 만들어 `/home/ubuntu/l4d2/left4dead2/cfg/server.cfg`에 마운트하세요.

### 명령줄로 완전히 대체하기

컨테이너 실행 시 이미지 이름 뒤에 인자(예: `...l4d2 +hostname "Vannah Hotel"`)를 넘기면 환경 변수 기반 설정을 건너뛰고 그 인자를 `srcds_run`에 그대로 전달합니다.
