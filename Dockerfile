FROM python:3.10.12-slim-bullseye

# Install system dependencies (matching install.sh)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    git \
    libmpv-dev \
    p7zip-full \
    pulseaudio \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS (matching install.sh)
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -ms /bin/bash ttbot

# Set working directory
WORKDIR /home/ttbot/TTMediaBot

# Add current directory to LD_LIBRARY_PATH so libTeamTalk5.so is found
# Add current directory to LD_LIBRARY_PATH so libTeamTalk5.so is found
ENV LD_LIBRARY_PATH=/home/ttbot/TTMediaBot:/home/ttbot/TTMediaBot/TeamTalk_DLL:$LD_LIBRARY_PATH

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (Cacheable)
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install "httpx>=0.28.1"

# Build argument to bust cache for core code and frequently-changing tools
ARG CACHEBUST=1

# Re-copy requirements just in case we need it below the cache line
COPY requirements.txt .

# Always ensure latest libraries and yt-dlp on every build
RUN pip install -U -r requirements.txt \
    && pip install "httpx>=0.28.1" \
    && pip install -U "yt-dlp[default] @ https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz"

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Adjust permissions (matching install.sh)
RUN chown -R ttbot:ttbot /home/ttbot/TTMediaBot \
    && chmod -R 775 .

# Switch to user
USER ttbot

# Run additional tools (as per original Dockerfile and README context)
# Run additional tools (as per original Dockerfile and README context)
# Run additional tools (as per original Dockerfile and README context)
RUN python tools/compile_locales.py

# Command to run the bot via entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["./TTMediaBot.sh", "-c", "data/config.json", "--cache", "data/TTMediaBotCache.dat", "--log", "data/TTMediaBot.log"]
