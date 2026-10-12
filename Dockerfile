# docker build -t l4d2 .
# docker build --pull --no-cache -t l4d2 .

FROM ubuntu:26.04 AS runtime

RUN dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get -y upgrade \
    && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
        ca-certificates \
        curl \
        lib32gcc-s1 \
        lib32stdc++6 \
        libsdl2-2.0-0:i386 \
        libcurl4t64:i386 \
        locales \
        tar \
    && locale-gen en_US.UTF-8 \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /tmp/dumps \
    && chown ubuntu:ubuntu /tmp/dumps

WORKDIR /home/ubuntu
USER ubuntu

FROM runtime AS server

RUN <<'EOF'
set -e
# Install steamcmd
mkdir -p .steam/sdk32/
ln -s ~/linux32/steamclient.so ~/.steam/sdk32/steamclient.so
curl https://media.steampowered.com/installer/steamcmd_linux.tar.gz | tar -xzvf -
EOF

RUN <<'EOF'
set -e
# Install game (L4D2 dedicated server app id 222860)
# update.txt is reused at runtime by entrypoint.sh
printf '%s\n' \
    'force_install_dir "/home/ubuntu/l4d2"' \
    'login anonymous' \
    'app_update 222860' \
    'quit' > update.txt
# https://github.com/ValveSoftware/steam-for-linux/issues/11522
# Linux depot alone fails with "Invalid platform"; download the Windows depot
# first, then validate as Linux. The platform directive must be the first line.
printf '%s\n' \
    '@sSteamCmdForcePlatformType windows' \
    'force_install_dir "/home/ubuntu/l4d2"' \
    'login anonymous' \
    'app_update 222860' \
    'quit' > first-install-windows.txt
printf '%s\n' \
    '@sSteamCmdForcePlatformType linux' \
    'force_install_dir "/home/ubuntu/l4d2"' \
    'login anonymous' \
    'app_update 222860 validate' \
    'quit' > first-install-linux.txt
# SteamCMD exits 0 and prints "Missing configuration" transiently on fresh
# installs, so check its output and retry.
run_steamcmd() {
    for _ in 1 2 3 4 5; do
        ./steamcmd.sh +runscript "$1" | tee /dev/stderr | grep -q 'Success!' && return 0
    done
    return 1
}
run_steamcmd first-install-windows.txt
run_steamcmd first-install-linux.txt
test -x /home/ubuntu/l4d2/srcds_run
rm first-install-windows.txt first-install-linux.txt
EOF

EXPOSE 27015/tcp 27015/udp

ENV HOSTNAME="" \
    PORT=27015 \
    STEAM_GROUP=0 \
    STEAM_GROUP_EXCLUSIVE=0 \
    DEFAULT_MAP="c1m1_hotel" \
    DEFAULT_MODE="coop" \
    GAME_TYPES="" \
    MOTD=0 \
    EXTRA_ARGS=""

ADD --chmod=755 entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
