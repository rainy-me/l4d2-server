import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# l4d2-server, l4d2-settings, l4d2-sourcemod 가 같은 부모 폴더에 나란히 있다고 가정
SM = HERE.parent / "l4d2-sourcemod"
SETTINGS = HERE.parent / "l4d2-settings"
# plugins/archive 는 배포하지 않음
SM_PLUGIN_DIRS = [SM / "plugins" / d for d in ("libs", "public", "rainy")]
OVERLAY = HERE / "overlay"
SERVERS_DIR = HERE / "servers"

# 아래 경로는 공통 빌드 폴더(임시 폴더) 기준
SCRIPTING = "addons/sourcemod/scripting"

# 서버에 복사되는 최상위 항목. 동기화할 때 이것들만 지우고 다시 만든다.
# 빌드나 overlay/<서버>/ 에 여기 없는 최상위 항목이 생기면 check_managed() 가 배포 전에 멈춘다.
MANAGED = ["addons", "cfg", "ems", "host.txt", "motd.txt"]
# 서버가 실행 중에 만든 데이터. 동기화해도 지우지 않고 남긴다.
PRESERVE = ["addons/sourcemod/logs", "addons/sourcemod/data/sqlite"]
# 복사하지 않는 파일 (빈 폴더를 git 에 남기기 위한 자리표시 등)
IGNORED = [".gitkeep"]
# 공통 빌드에서 빼는 항목 (빌드 폴더 기준)
# - metamod_x64.vdf: 64비트 Metamod 로더. L4D2 서버는 32비트라 로드에 실패하고
#   "wrong ELF class: ELFCLASS64" / "Unable to load plugin" 오류만 남긴다.
EXCLUDED = ["addons/metamod_x64.vdf"]


def all_servers() -> list[str]:
    """overlay/ 아래의 common 이외 폴더가 곧 서버 목록. 서버를 늘리려면 overlay/<이름>/ 을 만든다."""
    return sorted(
        p.name for p in OVERLAY.iterdir() if p.is_dir() and p.name != "common"
    )


def one(pattern: str) -> Path:
    """SM/base 아래에서 정확히 하나만 매칭되어야 함. 버전이 올라가도 여기를 고칠 필요가 없다."""
    matches = sorted((SM / "base").glob(pattern))
    if len(matches) != 1:
        found = ", ".join(m.name for m in matches) or "없음"
        sys.exit(f"{SM / 'base' / pattern} 는 정확히 하나여야 함 (찾은 것: {found})")
    return matches[0]


def subdirs(path: Path) -> list[Path]:
    """path 바로 아래의 폴더만 (README 같은 파일은 빼고) 이름순으로."""
    return sorted(p for p in path.iterdir() if p.is_dir())


def sources() -> list[tuple[Path, str]]:
    """(원본 경로, 빌드 폴더 기준 대상 경로) 목록. 뒤의 항목이 앞의 항목을 덮어쓴다."""
    return [
        (one("mmsource-*-linux"), "."),
        (one("sourcemod-*-linux"), "."),
        # plugins/<분류>/<이름>/ 은 gamedata/, scripting/ 등을 바로 담고 있음 → addons/sourcemod 기준
        *((p, "addons/sourcemod") for d in SM_PLUGIN_DIRS for p in subdirs(d)),
        # plugins_metamod/<이름>/ 은 addons/ 를 바로 담고 있음 → 루트 기준
        *((p, ".") for p in subdirs(SM / "plugins_metamod")),
        (SETTINGS / "cfg" / "sourcemod", "cfg/sourcemod"),
        (SETTINGS / "cfg" / "listenserver.cfg", "cfg"),
        (SETTINGS / "host.txt", "."),
        (SETTINGS / "motd.txt", "."),
        # 이 저장소에만 있는, 모든 서버 공통 파일. 마지막에 복사해서 우선 적용.
        (OVERLAY / "common", "."),
    ]


def copy(src: Path, dst: Path) -> None:
    if src.is_file():
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    else:
        shutil.copytree(
            src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*IGNORED)
        )


def build_common(build: Path) -> None:
    for src, dst in sources():
        if not src.exists():
            sys.exit(f"원본 없음: {src}")
        copy(src, build / dst)
        print(f"{src} -> {dst}")
    for rel in EXCLUDED:
        remove(build / rel)
        print(f"제외: {rel}")


def compile_plugins(build: Path) -> None:
    # 플러그인 .sp 파일을 plugins/ 로 바로 컴파일 (l4d2-sourcemod 의 reinstall.py 와 같은 목록 + overlay/common).
    scripting = build / SCRIPTING
    spcomp = scripting / "spcomp64"
    spcomp.chmod(0o755)
    sp_files = [
        *(sp for d in SM_PLUGIN_DIRS for sp in d.glob("*/scripting/*.sp")),
        *(OVERLAY / "common" / SCRIPTING).glob("*.sp"),
    ]
    # 빌드 폴더에서 컴파일하므로 파일 이름만 필요. 이름이 같으면 하나로 합친다.
    for sp in sorted({Path(p.name) for p in sp_files}):
        print(f"\n컴파일: {sp}", flush=True)  # spcomp 출력보다 먼저 찍히도록 flush
        subprocess.run(
            [spcomp, sp, "-iinclude", f"-o../plugins/{sp.stem}.smx"],
            cwd=scripting,
            check=True,
        )


def check_managed(build: Path, servers: list[str]) -> None:
    """MANAGED 에 없는 최상위 항목은 동기화 때 지워지지 않아 옛 파일이 계속 남는다.
    그런 항목이 있으면 서버 폴더를 건드리기 전에 멈춘다."""
    tops = {p.name for p in build.iterdir()}
    for server in servers:
        tops |= {p.name for p in (OVERLAY / server).iterdir() if p.name not in IGNORED}
    missing = sorted(tops - set(MANAGED))
    if missing:
        sys.exit(
            f"MANAGED 에 없는 최상위 항목: {', '.join(missing)} → sync.py 의 MANAGED 에 추가하세요"
        )


def remove(path: Path) -> None:
    """파일·폴더·심볼릭 링크를 지운다. 없으면 아무것도 하지 않는다."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def move(src: Path, dst: Path) -> None:
    """src 를 dst 로 옮긴다 (같은 파일시스템이라 rename 으로 충분)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)


def stash_preserved(dest: Path, keep: Path) -> None:
    """남길 데이터를 keep 으로 잠시 옮겨둔다.
    이전 실행이 중간에 죽어서 keep 에 이미 남아 있다면 그쪽이 진짜 데이터이므로 그대로 둔다."""
    for rel in PRESERVE:
        if (dest / rel).exists() and not (keep / rel).exists():
            move(dest / rel, keep / rel)


def restore_preserved(keep: Path, dest: Path) -> None:
    """keep 에 옮겨둔 데이터를 새로 배포된 dest 위에 되돌려놓고 keep 을 지운다."""
    for rel in PRESERVE:
        if (keep / rel).exists():
            remove(dest / rel)
            move(keep / rel, dest / rel)
    remove(keep)


def deploy(build: Path, server: str) -> None:
    """공통 빌드를 servers/<server>/ 로 복사하고 overlay/<server>/ 를 덮어쓴다. PRESERVE 는 유지."""
    dest = SERVERS_DIR / server
    keep = SERVERS_DIR / f".{server}.keep"

    stash_preserved(dest, keep)
    for name in MANAGED:
        remove(dest / name)

    copy(build, dest)
    copy(OVERLAY / server, dest)

    restore_preserved(keep, dest)
    print(f"배포: 공통 빌드 + overlay/{server}/ -> servers/{server}/")


def parse_args(servers: list[str]) -> list[str]:
    parser = argparse.ArgumentParser(
        description="공통 빌드(SourceMod + 플러그인 + 설정 + overlay)를 만들어 servers/<서버>/ 로 배포한다.",
    )
    parser.add_argument(
        "servers",
        nargs="*",
        metavar="server",
        help=f"배포할 서버 (생략하면 전부). 가능: {', '.join(servers)}",
    )
    args = parser.parse_args()
    unknown = sorted(set(args.servers) - set(servers))
    if unknown:
        parser.error(
            f"알 수 없는 서버: {', '.join(unknown)} (가능: {', '.join(servers)})"
        )
    return args.servers or servers


def main() -> None:
    targets = parse_args(all_servers())

    # 공통 파일은 임시 폴더에서 한 번만 만들고(컴파일 포함), 끝나면 자동으로 지운다.
    # 빌드가 끝까지 성공한 뒤에만 서버 폴더를 건드린다.
    with tempfile.TemporaryDirectory(prefix="l4d2-build-") as tmp:
        build = Path(tmp)
        build_common(build)
        compile_plugins(build)
        check_managed(build, targets)

        print()
        for server in targets:
            deploy(build, server)


if __name__ == "__main__":
    main()
