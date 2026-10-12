#!/bin/bash
# SteamCMD exits 0 and prints "Missing configuration" transiently, so check
# its output and retry. Give up after 5 tries and start with the files we have.
for _ in 1 2 3 4 5; do
    ./steamcmd.sh +runscript update.txt | tee /dev/stderr | grep -q 'Success!' && break
done

cd l4d2 || exit 50
GAME_DIR="left4dead2"

if [ $# -gt 0 ]; then
    ./srcds_run "$@"
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

    "${STARTUP[@]}"
fi