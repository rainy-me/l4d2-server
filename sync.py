import platform
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
# l4d2-server, l4d2-settings, l4d2-sourcemod 가 같은 부모 폴더에 나란히 있다고 가정
SM = HERE.parent / "l4d2-sourcemod"
SETTINGS = HERE.parent / "l4d2-settings"
SCRIPTING = HERE / "addons/sourcemod/scripting"
LOCAL_SCRIPTING = HERE / "local/addons/sourcemod/scripting"
ADMINS = HERE / "addons/sourcemod/configs/admins_simple.ini"
ADMIN_LINE = b'"STEAM_1:0:60846891"\t"99:z"'


def one(pattern: str) -> Path:
    """SM/API 아래에서 정확히 하나만 매칭되어야 함. 버전이 올라가도 여기를 고칠 필요가 없다."""
    (match,) = (SM / "API").glob(pattern)
    return match


def sources() -> list[tuple[Path, str]]:
    """(원본 경로, 이 저장소 기준 대상 경로) 목록. 뒤의 항목이 앞의 항목을 덮어쓴다."""
    return [
        (one("mmsource-*-linux"), "."),
        (one("sourcemod-*-linux"), "."),
        # Plugin/<이름>/ 은 gamedata/, scripting/ 등을 바로 담고 있음 → addons/sourcemod 기준
        *((p, "addons/sourcemod") for p in sorted((SM / "Plugin").iterdir())),
        # Plugin_metamod/<이름>/ 은 addons/ 를 바로 담고 있음 → 저장소 루트 기준
        *((p, ".") for p in sorted((SM / "Plugin_metamod").iterdir())),
        (SETTINGS / "cfg" / "sourcemod", "cfg/sourcemod"),
        (SETTINGS / "cfg" / "listenserver.cfg", "cfg"),
        (SETTINGS / "host.txt", "."),
        (SETTINGS / "motd.txt", "."),
        # 이 저장소에만 있는 파일 (저장소 루트와 같은 구조). 마지막에 복사해서 우선 적용.
        (HERE / "local", "."),
    ]


def copy_sources(entries: list[tuple[Path, str]]) -> None:
    # 원본에서 삭제된 파일이 여기서도 사라지도록, 복사 대상 폴더를 먼저 비운다.
    for d in ["addons", "cfg"]:
        shutil.rmtree(HERE / d, ignore_errors=True)

    for src, dst in entries:
        assert src.exists(), f"원본 없음: {src}"
        if src.is_file():
            shutil.copy2(src, HERE / dst)
        else:
            shutil.copytree(src, HERE / dst, dirs_exist_ok=True)
        print(f"{src} -> {dst}")


def compile_plugins(spcomp: Path) -> None:
    # 플러그인 .sp 파일을 plugins/ 로 바로 컴파일 (l4d2-sourcemod 의 reinstall.py 와 같은 목록 + local/).
    sp_files = [*(SM / "Plugin").rglob("scripting/*.sp"), *LOCAL_SCRIPTING.glob("*.sp")]
    for sp in sorted({p.name for p in sp_files}):
        print(f"\n컴파일: {sp}", flush=True)  # spcomp 출력보다 먼저 찍히도록 flush
        subprocess.run(
            [spcomp, sp, "-iinclude", f"-o../plugins/{Path(sp).stem}.smx"],
            cwd=SCRIPTING,
            check=True,
        )


def add_admin() -> None:
    # admins_simple.ini 는 위의 sourcemod 복사로 덮어써지므로, 매번 관리자를 다시 등록한다.
    text = ADMINS.read_bytes()
    if ADMIN_LINE in text:
        return
    eol = b"\r\n" if b"\r\n" in text else b"\n"  # 파일의 줄바꿈 방식에 맞춤
    prefix = b"" if not text or text.endswith(b"\n") else eol  # 마지막 줄과 붙지 않도록
    with ADMINS.open("ab") as f:
        f.write(prefix + ADMIN_LINE + eol)
    print(f"\nadmin 등록: {ADMINS}")


def main() -> None:
    copy_sources(sources())
    if platform.system() == "Windows":
        spcomp = one("sourcemod-*-windows/addons/sourcemod/scripting/spcomp.exe")
    else:
        spcomp = SCRIPTING / "spcomp64"
        spcomp.chmod(0o755)
    compile_plugins(spcomp)
    add_admin()


if __name__ == "__main__":
    main()
