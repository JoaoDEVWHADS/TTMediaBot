# 📋 Changelog — TTMediaBot

All notable updates to this fork are documented here, in reverse chronological order.

---

## 🆕 v2.4.6 — "Search Performance & Docker Optimization" *(06/13/2026)*

### ⚡ YouTube Music Search Speed Optimization

- **🔥 Persistent HTTP/2 Keep-Alive:**
  Configured `httpx.Limits(keepalive_expiry=30.0)` in `ytm.py` and reduced the background connection keeper sleep interval to `4 seconds`. This keeps the YTM session warm in the background and drops search response latency from ~1000ms to ~500ms.

- **⚡ HTTP/2 Support (YTM):**
  Integrated `httpx[http2]` inside `ytm.py` to enable HTTP/2 multiplexing, header compression, and connection persistence.

- **⏱️ YouTube Traditional (`yt.py`) Keep-Alive:**
  Added a background connection keeper to the standard YouTube service, dropping search pre-warming and query latencies from ~3.5 seconds to ~800ms.

### 🐳 Optimized Docker Rebuild Flow (Zero Downtime)

- **🚀 Rebuild Before Stop:**
  Modified `ttbotdocker.sh` and `update.sh` to run `docker build` first while the bot containers are still online. The containers are stopped and recreated ONLY after the build completes, reducing user downtime from 30+ seconds to just 2-3 seconds.

### 🔧 Permissions & Updater Polish

- **🛡️ Ignore File Permission Drifts in Git:**
  Added `git config core.fileMode false` dynamically in `update.sh`, `auto_updater.sh`, `install.sh`, and `install_git_clone.sh`. This ensures that recursive permission adjustments (`chmod`) performed by the installer or updater do not cause text or translation files (such as `docs/README.*.md`) to appear as unstaged mode changes (`new mode 100755`) on users' systems.

---

## 🆕 v2.4.5 — "Multi-Distribution Compatibility" *(06/13/2026)*

### 🖥️ Shell Scripts & Package Manager Abstraction

- **🌐 Dynamic Package Manager Detection:**
  Added the `install_packages` function in `install_git_clone.sh` and custom package manager mapping in `install.sh` to dynamically handle system packages for Debian/Ubuntu (APT), Fedora/RHEL/CentOS (DNF/YUM), Arch Linux (Pacman), openSUSE (Zypper), and Alpine (APK).

- **🐳 Docker Manager (`ttbotdocker.sh`) Generalization:**
  Upgraded dependency checks to install `jq` on Zypper and APK systems, wrapped all `systemctl` calls to avoid crashing on systemd-less environments, and replaced hardcoded `apt-get` calls in `uninstall_all` with appropriate commands for the detected package manager.

---

## 🆕 v2.4.4 — "Stability & Search Optimization" *(06/13/2026)*

### ⚡ Performance & Connectivity

- **🎵 YouTube Music Keep-Alive (Lag Reduction):**
  Added a background connection-warming thread in `ytm.py` that pings YouTube Music (`/generate_204`) every 15 seconds. This keeps the TCP/SSL connection warm, dropping latency by eliminating the TLS/SSL handshake penalty and lowering search times from ~1000ms to ~650ms.

- **🔍 Thread-Safe YT Search Event Loop:**
  Refactored `yt.py` to run async searches thread-safely on a persistent background event loop (`self._loop`) using `asyncio.run_coroutine_threadsafe(...).result()`. This resolves intermittent "Event loop is closed" errors during search execution.

### 🐛 Stability & Crash Prevention

- **🛡️ TaskProcessor Resilience:**
  Wrapped task execution inside `task_processor.py` in a `try-except` block. If resolving/playing a track fails, the worker thread no longer crashes, keeping the commands queue and playback system fully operational.

- **🚫 Unreleased / Private Video Loop Protection:**
  Added a `self._fetch_failed` state in `track.py` to prevent the bot from entering infinite resolution retries when trying to play private, deleted, or unreleased Premiere videos (such as videos that haven't premiered yet).

### 📋 Documentation & Metadata

- **🌐 Multi-Language Documentation Restructuring:**
  Moved `CHANGELOG.md` to `docs/CHANGELOG.md` and created 6 naturally translated versions of the README (`docs/README.en.md`, `docs/README.pt.md`, `docs/README.es.md`, `docs/README.es-419.md`, `docs/README.ar.md`, `docs/README.ru.md`).
  Replaced the root `README.md` with a clean, H1-level language entrypoint gateway to select the preferred documentation translation.

- **🏷️ Repository Metadata Update:**
  Updated the repository description on GitHub to: *"An enhanced music streaming bot for TeamTalk Servers with native YouTube Music support and Docker orchestration."*

---

## 🆕 v2.4.3 — "Node.js v22 Upgrade" *(06/11/2026)*

### 🐳 Docker & Dependencies Update

- **🟢 Node.js Upgrade to v22:**
  Upgraded the Node.js version installed in the Dockerfile from v20 to v22. This matches the new minimum JavaScript runtime requirements introduced in the latest `yt-dlp` (2026.06.09+), restoring YouTube signature solving (n-challenge) and resolving the "Requested format is not available" errors.

---

## 🆕 v2.4.2 — "Backup, Restore & Logs Cleanup" Update *(06/09/2026)*

### 🐳 Docker Manager (`ttbotdocker.sh`) Extensions

- **📦 Backup & Restore System (Portability):**
  Added a portable configuration and cache backup/restore system. Backups are saved as compressed `.tar.gz` files containing all bots configurations, cookies, and cache in a dedicated `backups/` directory. Restoring dynamically cleans old environments, extracts configs, and reconstructs Docker containers on any host machine.
  
- **🧹 Log Cleanup Option:**
  Added a quick-clear command that purges all `*.log` files within bot data folders in a single action, reclaiming storage space.

- **⚙️ Menu Rearrangement:**
  Reordered the "Manage Bots" submenu options: "Backup / Restore Bots" is now option **10**, "Clear All Bot Logs" is option **11**, and the "Return to Main Menu" (previously option 10) has been moved to option **12**.

---

## 🆕 v2.4.1 — "YTM Search Performance Fix" Update *(06/05/2026)*

### ⚡ Connection Pre-warming & Startup Polish

- **⏱️ Docker Container Startup Settling:**
  Added an initial `5 seconds` delay to the background pre-warming threads in both YouTube (`yt.py`) and YouTube Music (`ytm.py`) services. This allows the Docker container network interfaces and internal DNS resolvers to fully initialize before starting requests.
  
- **🔄 Robust Pre-warming Retry Mechanism:**
  Introduced a 3-attempt retry loop (with a 5-second interval) for the initial search request. This prevents the connection pools from failing permanently if the network takes a few extra seconds to boot.
  
- **📢 Improved Logging & Diagnostics:**
  Warmed-up connection attempts are now explicitly tracked via logs. If the pre-warming fails all retries, it raises a warning/error in the logs instead of failing silently at debug level.

- **⚙️ Default Service Config Update:**
  Changed the default search and stream service from YouTube (`yt`) to YouTube Music (`ytm`) in `config.json` and `config_default.json` templates to provide the music-oriented experience by default.

---

## 🆕 v2.4.0 — "Universal Docker & Configurable Search" Update *(06/05/2026)*

### 🖥️ Native ARM64 Compatibility & Code Cleanup

- **🤖 Platform Auto-detection:**
  Added system architecture auto-detection (`uname -m`) to `install_git_clone.sh`. The installer now automatically selects and downloads the appropriate TeamTalk library binary (`ttarm.zip` for ARM64 / ARM devices, or the standard `TeamTalk_DLL.zip` for x86_64 systems).

- **🐳 Docker & Host Dependencies for ARM:**
  Added the `libportaudio2` library dependency to `Dockerfile` and `install.sh`. This resolves the missing `libportaudio.so.2` runtime link errors when executing the ARM64 compiled TeamTalk SDK inside the Docker container or directly on the host system.

- **⚙️ Conditional Package Installation (Minimal Footprint):**
  Refactored dependency installation logic. The `libportaudio2` package is now conditionally installed ONLY when an ARM environment (`arm64`/`armhf`/`aarch64`) is detected. This ensures that `x86_64` environments remain minimal and untouched by ARM-specific runtime dependencies.

- **🧹 Code Cleanup:**
  Removed redundant Docker installation checks from `install_git_clone.sh`, delegating all environment dependencies verification and setup to `ttbotdocker.sh`.

### 🔍 Configurable Search Results Default

- **⚙️ Config-Driven Search Limits:**
  Added the `search_results: int = 1` option to both YouTube (`yt`) and YouTube Music (`ytm`) configuration models in `models.py`, defaulted in `config.json` and `config_default.json`.
  
- **🔄 Dynamic Fallback in Services:**
  Updated the base service search interface in `__init__.py` and implementations in `yt.py` and `ytm.py` to use the configuration-defined default search results limit (1) when the dynamic limit parameter is omitted.

- **🔢 Search Results Mode Command Updates:**
  Changed the default volatile search count for the `sr`/`slc`/`sl` commands from `5` to `1` in `__init__.py` and `user_commands.py`.

### 🐳 Universal Docker Setup

- **🚀 Support for Any Linux Distribution:**
  Upgraded the Docker environment checks in `ttbotdocker.sh` to use the official universal `get.docker.com` script. This enables automatic setup of Docker Engine across all major distributions (Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky, Alma, Raspbian).
  
- **🧹 Installer Script Cleanup:**
  The downloaded `get-docker.sh` installer script is automatically deleted immediately after completion to keep the host directory clean.

- **📦 Multi-Distribution dependency installer:**
  Added fallback detection for package managers (`apt`, `dnf`, `yum`, `pacman`) to install the `jq` dependency dynamically on any supported Linux distribution.

---

## 🆕 v2.3.0 — "Dynamic SSL Trust" Update *(05/30/2026)*

### 🔒 Dynamic SSL Trust & Peer Verification Bypass

- **🛡️ Auto-fetching SSL Certificates:**
  When connecting to an encrypted TeamTalk server (`encrypted: true`), the bot now automatically attempts to fetch the server's certificate dynamically over the network if a local CA certificate (`ttservercert.pem`) is not configured.

- **✅ Local and Third-Party Server Support:**
  The dynamically fetched certificate is temporarily trusted via OpenSSL/ACE SSL verification, allowing seamless encrypted connections to self-signed or third-party servers without manual certificate management (mirroring the Windows client behavior).

- **🔧 Exposed `setEncryptionContext` in Wrapper:**
  Exposed the C-level `TT_SetEncryptionContext` function inside `TeamTalkPy` wrapper as `setEncryptionContext`, enabling programmatic control over SSL contexts directly from Python.

---

## 🆕 v2.2.0 — "Link-Based Downloading" Update *(05/23/2026)*

### 🔗 Link-Based Downloading Commands

- **➕ `aad LINK` Command — Add Link:**
  Adds a single media link/URL to the user's custom download list.

- **➕ `ad LINK1 LINK2 ...` Command — Add Multiple Links:**
  Adds multiple space-separated links to the download list at once.

- **📜 `ld` Command — List Links:**
  Displays a numbered list of all links currently in the user's download list.

- **🗑️ `rd NUMBER_OR_LINK` Command — Remove Link:**
  Removes a link from the download list by its index or URL string.

- **📥 `ldd LINK` Command — Download Direct:**
  Directly downloads a link asynchronously and uploads it to the TeamTalk channel.

- **⚡ `ads` Command — Download and Upload List:**
  Asynchronously downloads the user's link list. Prompts the user to choose between:
  1. Downloading individually (Normal sequential upload)
  2. Compressing all resolved tracks into a single ZIP archive and uploading it.

- **💾 `adsc` Command — Toggle Local VPS Download Mode:**
  Toggles local download mode for the `ads` command (volatile, resets on bot restart).
  When active, downloads are saved locally to the VPS filesystem under `data/Downloads/music/` (Option 1) or `data/Downloads/zips/` (Option 2) instead of uploaded to TeamTalk, and are excluded from auto-deletion. Outputs a final translated status report.

### 🌍 100% Localization & Translations

- Fully translated and compiled all 27 new strings (commands, prompts, errors, success reports) across all 7 supported languages: Arabic (`ar`), Spanish (`es`), Hungarian (`hu`), Indonesian (`id`), Portuguese-Brazil (`pt_BR`), Russian (`ru`), and Turkish (`tr`).

### 🐛 Core Uploader & Stability Fixes

- **⏱️ Non-blocking Deletion Timer:**
  Changed the file deletion timer in the uploader to run in a background daemon thread, preventing batch downloads from blocking.

- **🛡️ Server Error Infinite Loop Fix:**
  Fixed a major bug where unhandled server error codes (e.g. `FileAlreadyExists`) would lock the uploader in an infinite loop. It now breaks and handles errors gracefully.

---

## 🆕 v2.1.0 — "Smart Search & Docker Polish" Update *(05/21/2026)*

### 🔍 New Bot Commands — Search Results Mode

- **🔎 New `sr` Command — Search Results Mode Toggle:**
  When active, the `p QUERY` command no longer plays immediately — it instead shows a **numbered list** of results. Use `sr on`, `sr off`, or just `sr` to toggle. Use `sc` to save the setting permanently to `config.json`.

- **🎯 New `sl NUMBER` Command — Select from Search Results:**
  After a search (with `sr` mode active), pick exactly which track to play by its number. Results are stored **per user** and cleared after selection for a clean experience.

- **🔢 New `slc NUMBER` Command — Set Search Results Count:**
  Controls how many results are displayed per search when `sr` mode is active. Defaults to **5**. Use `slc` alone to check the current count. Resets to 5 on bot restart.

### 🐳 Docker Manager (`ttbotdocker.sh`) Improvements

- **⏱️ File Deletion Timer — Create Bot:**
  When creating a new bot, the script now reads `general.delete_uploaded_files_after` from `config.json` and offers to customize the value per bot. `0` = never delete. Supports any duration in seconds.

- **⏱️ File Deletion Timer — Bulk Update:**
  New **Option 6** in the Bulk Update Configuration menu allows changing `delete_uploaded_files_after` across bots without rebuilding. Option 7 ("Everything") now also includes the timer.

- **🎯 Selective Bot Update — Bulk Update now targets specific bots:**
  After choosing what to change, a new targeting menu appears:
  - **Option 1:** Apply to ALL bots
  - **Option 2:** Apply to a **single specific bot** (from a numbered list)
  - **Option 3:** Apply to a **custom subset** (space-separated numbers)

  Only selected bots are updated **and restarted** — other running bots are not touched.

### 📚 Documentation

- **📋 CHANGELOG extracted from README:**
  Full version history moved to a dedicated [`CHANGELOG.md`](CHANGELOG.md) file. The README now shows only the latest update with a link to the full history.

---

## 🆕 v2.0.0 — "The Video" Update *(05/14/2026)*


- **🎥 New `dlv` Command:** Download current track as **Video** (.mp4) directly to the channel.
- **🧠 Smart Uploader 2.0:** Rewritten uploader module with intelligent file discovery. If the expected format isn't found, it automatically searches for alternative extensions (.mkv, .webm, etc.) before failing.
- **🎞️ Forced MP4 Encoding:** Optimized video downloads to force MP4 merging, ensuring maximum compatibility with all media players.
- **🌍 Global Video Support:** Full localization for the `dlv` command across all 7 supported languages (PT-BR, ES, HU, ID, RU, TR, AR).
- **🛠️ Robustness Fix:** Resolved naming inconsistencies between `yt-dlp` output and uploader expectations.

---

## 🆕 v1.9.0 — "Performance & Cleanup" Update *(05/11/2026)*

- **🧹 Deep Docker Cleanup:** Added a powerful cleanup option (Option 7) to `ttbotdocker.sh` that wipes stopped containers, unused images, build cache, and even host system logs (`journalctl`) to reclaim maximum disk space.
- **📉 200MB+ Image Reduction:** Drastically reduced Docker image size (from ~1.6GB to ~1.4GB) by implementing:
  - **`.dockerignore`:** Prevents bloating the image with `.git`, `bots/` folders, and other host-only files.
  - **`--no-cache-dir`:** Optimized PIP installations to not store installer caches inside the container.
- **🚀 Faster Builds:** The new `.dockerignore` prevents uploading unnecessary files to the Docker daemon, making the build process more efficient.
- **📊 Real-time Disk Reclaim:** Cleanup process now includes `buildx prune` and system journal vacuuming for a truly "zero-clutter" environment.

---

## 🆕 v1.8.0 — "Universal Language" Update *(05/10/2026)*

- **🌍 Arabic Support Added:** Full native support for Arabic (`ar`) language, including right-to-left (RTL) considerations for messages.
- **💯 100% Localization:** Achieved 100% translation coverage across all supported languages (PT-BR, ES, HU, ID, RU, TR, AR).
- **🆕 Queue & Playlist i18n:** All new features (Queue system, Playlist downloads) are now fully localized in every language.
- **🧹 Systematic Audit:** Complete cleanup of all translation catalogs, resolving fuzzy strings and missing translations for a seamless global experience.

---

## 🆕 v1.7.0 — "Queue System" Update *(05/09/2026)*

> A huge shoutout and massive credits to **ericoamico** for his incredible dedication and a full week of hard work in developing this amazing feature! All credits for the new queue system go to him.

- **🗂️ Advanced Queue System:** You can now queue multiple tracks to play sequentially!
- **➕ Add to Queue:** Use the `qa` command to search for a track and seamlessly add it to your queue.
- **📜 View Queue:** Check what's playing next with the `ql` command to list all queued tracks.
- **🗑️ Queue Management:** Use `qr [number]` to remove a specific song, or `qc` to clear the entire queue at once.
- **⏭️ Smart Skip:** The new `qs` command skips the current track and instantly plays the next one from the queue.

---

## 🆕 v1.6.0 — "Playlist Power-Up" Update *(05/06/2026)*

- **📦 New `dlp` Command:** Download entire YouTube/YouTube Music playlists and albums as organized ZIP archives directly to the TeamTalk channel.
- **📂 Intelligent ZIP Structure:** Archives now wrap contents inside a subfolder named after the playlist/album, ensuring a clean extraction process.
- **🧠 Smart Naming Engine:** Automatically distinguishes between Official Albums (`Album - Artist.zip`) and personal Playlists (`Playlist Name.zip`) based on link patterns and metadata.
- **🕵️ PM Progress Reporting:** Live track-by-track download progress is sent via **Private Message (PV)** to keep the channel clean while keeping the user informed.
- **📊 Active Status Check:** Typing `dlp` without arguments during an active download returns the current real-time status of the process.
- **💾 Permanent Channel Storage:** Playlist ZIPs are stored permanently in the channel (not auto-deleted like `dl` files), building a community library.
- **🌍 Full Localization (i18n):** All new features and status messages fully localized for Portuguese, Spanish, Turkish, and Russian.
- **🛠️ Enhanced Metadata Scanning:** Aggressive multi-track scanning to extract correct artist and album names even from tricky direct links.

---

## 🆕 v1.5.0 — "Global Expansion" Update *(05/03/2026)*

- **🌍 Full i18n Localization:** Completed full translation and standardization for PT-BR, Turkish (TR), Spanish (ES), and Indonesian (ID). All core commands and system messages are now fully localized.
- **🎧 Studio Quality Audio (320kbps):** Upgraded audio streaming and transcoding to 320kbps MP3 by default for superior sound quality.
- **🔄 Bulletproof Auto-Updater:** Major overhaul of the update system. Resolved infinite loops, fixed remote detection issues, and ensured updates work even with local file changes.
- **⚡ Optimized Extraction:** Fixed YouTube signature errors and optimized ServiceManager for faster track loading and reduced latency.
- **🎮 Polling Optimization:** Reduced auto-updater polling interval to 20 seconds for near-instant synchronization with the repository.
- **🧹 Robust File Lifecycle:** Enhanced cleanup logic for temporary files and cookies, ensuring a zero-footprint operation after every request.

---

## 🆕 v1.3.1 — "Zero-Footprint" Update *(04/24/2026)*

- **🛡️ Auto-Cleanup for Cookies:** When pasting cookies, the temporary file created in `/tmp` is now automatically deleted immediately after use, ensuring zero disk footprint and maximum privacy.
- **🎮 Auto-Update Controller (`masc.sh`):** New dedicated menu (Main Menu option 6) to enable/disable automatic updates with systemd masking for 100% persistence.
- **🍪 Cookie Paste Option:** Paste cookies directly into the terminal; the script auto-normalizes formatting (spaces to tabs) and sets correct file permissions.
- **🛡️ Per-Request Cookie Lifecycle:** Each download or stream request now creates a unique, volatile copy of your `cookies.txt` in `/tmp`. These files are deleted immediately after use, ensuring 100% privacy and zero disk clutter.
- **🐳 Dockerfile Optimization:** Updated `httpx` to version `0.28.1+` and resolved dependency conflicts, ensuring a stable and compatible network stack.
- **🧵 Thread-Safe Authentication:** The temporary cookie mechanism is now fully thread-safe, allowing multiple bots to operate without file access conflicts.

---

## 🆕 v1.1 — "Reliability & Quality" Update *(04/23/2026)*

- **🚀 Automated Background Updates:** Systemd service monitors GitHub every 20 seconds.
- **🎵 High-Quality MP3:** Migrated to 192kbps MP3 by default.
- **✅ Improved Permissions:** Refined upload logic for non-privileged bots.

---

## 🆕 YouTube Music Support *(03/19/2026)*

- **YouTube Search API Integration:** Uses the YouTube Search API for fast and reliable music discovery
- **Optimized Libraries:**
  - YouTube uses `py-yt-search` — a fast and modern Python library for YouTube searches
  - YouTube Music uses `ytmusicapi` — the official YouTube Music API library
  - Both services use `yt-dlp` for audio extraction
- **Performance Focus:** Designed to run with minimal bottlenecks, ensuring smooth playback and quick search results
- **Unified Cookie System:** Both YouTube and YouTube Music use the same cookies configuration for authentication
- **📦 Playlist & Album Downloads:** Full support for downloading entire collections via the `dlp` command with metadata-aware naming
- **🕵️ Real-time PM Progress:** Stay updated on your downloads without cluttering the channel
