# l4d2-server

Left 4 Dead 2 데디케이티드 서버를 띄우기 위한 저장소입니다.

- `Dockerfile`  
  SteamCMD로 L4D2 서버를 설치한 기본 이미지(`l4d2`). 설정은 환경 변수로 받습니다.  
  자세한 사용법은 [README_Dockerfile.md](README_Dockerfile.md) 참고.
- `docker-compose.yml`  
  Linux용. `addons/`, `cfg/` 등을 바인드 마운트해 서버를 띄웁니다.
- `docker-compose-win.yml` / `Dockerfile.win`  
  Windows(Docker Desktop)용. 마운트 대신 파일을 이미지에 복사합니다.
- `sync.py`  
  별도 저장소(`l4d2-sourcemod`, `l4d2-settings`)에서 플러그인, 설정 파일을 가져와서 이 저장소에 반영합니다.

## Rainy's 리포지토리

- [l4d2-server](https://github.com/rainy-me/l4d2-server): Left 4 Dead 2 데디케이티드 서버 구성 모음
- [l4d2-settings](https://github.com/rainy-me/l4d2-settings): Left 4 Dead 2 설정 모음
- [l4d2-sourcemod](https://github.com/rainy-me/l4d2-sourcemod): Left 4 Dead 2 SourceMod 구성 모음
