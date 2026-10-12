#!/bin/bash
# SteamCMD exits 0 and prints "Missing configuration" transiently, so check
# its output and retry. Give up after 5 tries and start with the files we have.
# No grep -q: it would close the pipe on the first match and kill SteamCMD
# before it finishes.
for _ in 1 2 3 4 5; do
    ./steamcmd.sh +runscript update.txt | tee /dev/stderr | grep 'Success!' >/dev/null && break
done

cd l4d2 || exit 50

# srcds_linux has no SIGTERM handler, so "docker stop" would kill it on the
# spot (no plugin unload, no log flush). Feed the console through a FIFO
# instead, and type "quit" into it when SIGTERM arrives.
run_server() {
    local console=/tmp/console.$$ relay server status
    mkfifo "$console"
    exec 3<>"$console" 4<&0 # 3: held open both ways so the server never sees EOF
    rm "$console"
    cat <&4 >&3 & # relay our stdin (docker attach) to the server console
    relay=$!
    "$@" <&3 &
    server=$!
    trap 'echo quit >&3' TERM
    # wait returns early when the trap fires, so keep waiting until the server is gone
    while kill -0 "$server" 2>/dev/null; do
        wait "$server"
        status=$?
    done
    kill "$relay" 2>/dev/null
    return "$status"
}

if [ $# -gt 0 ]; then
    run_server ./srcds_run "$@"
else
    STARTUP=("./srcds_run")
    STARTUP+=("+sv_logecho 1")

    if [ -n "${HOSTNAME}" ]; then
        STARTUP+=("+hostname \"${HOSTNAME}\"")
    fi

    if [ "${PORT:-0}" -gt 0 ]; then
        STARTUP+=("-port $PORT")
    fi

    if [ "${STEAM_GROUP}" -gt 0 ]; then
        STARTUP+=("+sv_steamgroup ${STEAM_GROUP}")
        if [ "${STEAM_GROUP_EXCLUSIVE}" = "1" ]; then
            STARTUP+=("+sv_steamgroup_exclusive 1")
        fi
    fi

    STARTUP+=("+map \"$DEFAULT_MAP $DEFAULT_MODE\"")

    if [ -n "${GAME_TYPES}" ]; then
        STARTUP+=("+sv_gametypes \"${GAME_TYPES}\"")
    fi

    if [ "${MOTD}" = "0" ]; then
        STARTUP+=("+motd_enabled 0")
    fi

    if [ -n "${EXTRA_ARGS}" ]; then
        STARTUP+=("${EXTRA_ARGS}")
    fi

    run_server "${STARTUP[@]}"
fi
