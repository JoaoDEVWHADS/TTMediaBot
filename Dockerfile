# The bundled TeamTalk 5.8.1 SDK still needs OpenSSL 1.1.
# Keep only its compatibility libraries; the main image uses Trixie packages.
FROM debian:bullseye-slim AS teamtalk-compat
ARG CACHEBUST=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends libssl1.1 \
    && mkdir /compat \
    && find /usr/lib -type f \( -name 'libssl.so.1.1' -o -name 'libcrypto.so.1.1' \) -exec cp '{}' /compat/ \; \
    && test -s /compat/libssl.so.1.1 \
    && test -s /compat/libcrypto.so.1.1 \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.13-slim-trixie

# The manager supplies a fresh value for explicit image rebuilds. Place this
# before dependency installation so moving Node dependencies are refreshed too.
ARG CACHEBUST=1
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        curl gnupg git libmpv2 p7zip-full pulseaudio ca-certificates ffmpeg procps unzip \
    && ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "armhf" ]; then \
        apt-get install -y --no-install-recommends libportaudio2; \
       fi \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /opt/bgutil-provider \
    && cd /opt/bgutil-provider/server \
    && npm ci \
    && npx tsc

COPY --from=teamtalk-compat /compat/ /opt/teamtalk-compat/
RUN useradd -ms /bin/bash ttbot
WORKDIR /home/ttbot/TTMediaBot
ENV LD_LIBRARY_PATH=/opt/teamtalk-compat:/home/ttbot/TTMediaBot:/home/ttbot/TTMediaBot/TeamTalk_DLL

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --upgrade -r requirements.txt "httpx[http2]>=0.28.1" "python-mpv==1.0.8"

COPY youtube_bridge/package.json youtube_bridge/package.json
RUN npm install --prefix youtube_bridge --omit=dev

COPY . .
# The vendored binding predates MPV's loadfile argument change. Replace it with
# the installed binding after COPY, keeping both imports and the library aligned.
RUN python -c "import shutil; from importlib.metadata import distribution; shutil.copyfile(distribution('python-mpv').locate_file('mpv.py'), 'mpv.py')" \
    && chmod +x entrypoint.sh \
    && chown -R ttbot:ttbot /home/ttbot/TTMediaBot \
    && chmod -R 775 .

USER ttbot
RUN python tools/compile_locales.py
ENTRYPOINT ["./entrypoint.sh"]
CMD ["./TTMediaBot.sh", "-c", "data/config.json", "--cache", "data/TTMediaBotCache.dat", "--log", "data/TTMediaBot.log"]
