# 📋 Changelog — TTMediaBot

All notable updates to this fork are documented here, in reverse chronological order.

---

## 🆕 v2.4.0 — "ARM64 Architecture Support" Update *(06/05/2026)*

### 🖥️ Native ARM64 Compatibility

- **🤖 Platform Auto-detection:**
  Added system architecture auto-detection (`uname -m`) to [install_git_clone.sh](file:///home/admin/joao/TTMediaBot/install_git_clone.sh). The installer now automatically selects and downloads the appropriate TeamTalk library binary (`ttarm.zip` for ARM64 / ARM devices, or the standard `TeamTalk_DLL.zip` for x86_64 systems).

- **🐳 Docker & Host Dependencies for ARM:**
  Added the `libportaudio2` library dependency to [Dockerfile](file:///home/admin/joao/TTMediaBot/Dockerfile) and [install.sh](file:///home/admin/joao/TTMediaBot/install.sh). This resolves the missing `libportaudio.so.2` runtime link errors when executing the ARM64 compiled TeamTalk SDK inside the Docker container or directly on the host system.

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
