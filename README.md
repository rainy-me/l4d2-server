# l4d2-server

Left 4 Dead 2 데디케이티드 서버를 띄우기 위한 저장소입니다.

- `Dockerfile`  
  SteamCMD로 L4D2 서버를 설치한 기본 이미지(`l4d2`). 설정은 환경 변수로 받습니다.  
  자세한 사용법은 [README_Dockerfile.md](README_Dockerfile.md) 참고.
- `docker-compose.yml`  
  서버마다 `servers/<서버>/` 의 `addons/`, `cfg/` 등을 바인드 마운트해 서버를 띄웁니다.  
  서버끼리 파일을 공유하지 않으므로 로그, DB, 자동 생성 설정이 섞이지 않습니다.
- `sync.py` / `sync.sh`  
  별도 저장소(`l4d2-sourcemod`, `l4d2-settings`)에서 플러그인, 설정 파일을 가져와 임시 폴더에서 한 번 빌드(플러그인 컴파일 포함)한 뒤,
  `servers/<서버>/` 로 복사합니다. `./sync.sh server1` 처럼 서버를 지정하면 그 서버만 갱신합니다.  
  `addons/sourcemod/logs`, `addons/sourcemod/data/sqlite` 는 서버가 만든 데이터라 동기화해도 남겨둡니다.
- `overlay/`  
  이 저장소에만 있는 파일. `overlay/common/` 은 모든 서버에, `overlay/<서버>/` 는 그 서버에만 적용됩니다(뒤에 적용되어 덮어씀).  
  서버를 늘리려면 `overlay/<서버>/` 폴더를 만들고 `docker-compose.yml` 에 서비스를 추가하세요.  
  플러그인 소스(`.sp`)는 `overlay/common/` 에만 두세요. 컴파일은 공통 빌드에서 한 번만 합니다.
- `접속자_가이드.md`  
  서버에 접속하는 사람이 쾌적하게 플레이하기 위한 클라이언트 준비 사항.  
  자세한 내용은 [접속자\_가이드.md](접속자_가이드.md) 참고.

## Rainy's 리포지토리

- [l4d2-server](https://github.com/rainy-me/l4d2-server): Left 4 Dead 2 데디케이티드 서버 구성 모음
- [l4d2-settings](https://github.com/rainy-me/l4d2-settings): Left 4 Dead 2 설정 모음
- [l4d2-sourcemod](https://github.com/rainy-me/l4d2-sourcemod): Left 4 Dead 2 SourceMod 구성 모음
