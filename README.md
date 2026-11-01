# TTMediaBot

**Hello! I am João Almeida.** Welcome to my **TTMediaBot** fork, a comprehensive media streaming bot for TeamTalk 5. This repository is focused on delivering constant improvements, stability, and new features, such as exclusive support for YouTube Music.

> 🔗 **My Repository:** [https://github.com/JoaoDEVWHADS/TTMediaBot](https://github.com/JoaoDEVWHADS/TTMediaBot)

---

> **Note:** This repository is a fork of the [original TTMediaBot](https://github.com/gumerov-amir/TTMediaBot).

A feature-rich media streaming bot for TeamTalk 5, capable of playing music from various services (YouTube, YouTube Music, local files, URLs) with advanced control features.


## 📋 Changes from Original

This fork includes several modifications and optimizations:

- **Removed Services:** Yandex Music and VK integration have been removed
- **TeamTalk SDK Upgrade:** Updated to TeamTalk SDK 5.8.1 for improved performance
- **YouTube.js Bridge Architecture:** Replaced `yt-dlp` and `py-yt-search` with a persistent `YouTube.js` (`youtubei.js`) bridge, removing repeated command-line extraction from the playback path.
- **Shared Multi-Bot Backend:** All bot containers now use one managed YouTube service containing the bridge and PO-token provider. Per-bot cookies remain isolated, while sessions, resolved streams, and in-flight requests are efficiently reused.
- **ARM64 Architecture Support:** Added native support for ARM64 architecture (such as Raspberry Pi and AWS Graviton servers) with automatic platform detection and library downloads during installation.
  > [!NOTE]
  > On `x86_64` systems, the installation remains untouched and minimal. On `ARM` systems, the installer and Dockerfile conditionally install additional dependencies (such as `libportaudio2`) required by the ARM version of the TeamTalk SDK to run.
- **Universal Linux Distribution Support:** The installer (`ttbotdocker.sh` / `install_git_clone.sh`) now dynamically supports automatically setting up Docker, `ffmpeg`, and dependencies on any major distribution (Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux, Raspbian, Arch, etc.) using the official universal installer and dynamic package manager fallbacks for `jq`.
- **Docker Containerization:** The image uses Debian Trixie, Python 3.13, Node.js 24, and current stable-distribution playback packages. The bundled TeamTalk 5.8.1 SDK retains isolated OpenSSL 1.1 compatibility libraries.
- **Proven Stability:** Since I first encountered this bot in 2021, the adaptations made to work around YouTube's restrictions, combined with the optimizations from 2021/2022, have proven to be excellent and reliable

## 🆕 Latest Updates

To view the complete history of updates, including all new features, bug fixes, and optimizations, please check the changelog.

> 📋 **[See full changelog →](CHANGELOG.md)**

## 🏗️ YouTube Backend Migration and Shared-Service Architecture

### Why `yt-dlp` was removed

YouTube playback progressively acquired additional validation layers. Playable URLs can require transformation of the player JavaScript `n` parameter and signature cipher, while some clients and Google Video Server (GVS) requests also require a Proof of Origin (PO) Token. These are separate mechanisms: deciphering `n/sig` produces a valid signed media URL, whereas a PO Token attests the request's origin and may be bound to its session or content. The [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) notes that a missing token can result in HTTP 403 responses for affected clients, and the [YouTube.js player implementation](https://github.com/LuanRT/YouTube.js/blob/main/src/core/Player.ts) handles signature deciphering and PO-token attachment as distinct operations.

Before the migration, TTMediaBot adapted `yt-dlp` to those restrictions by embedding the [`bgutil-ytdlp-pot-provider`](https://github.com/Brainicism/bgutil-ytdlp-pot-provider), its plugin, and a Node.js token server in every bot container. The provider improved compatibility but could not guarantee that every 403 or bot check would disappear. Meanwhile, each unresolved track still started a separate `yt-dlp` extraction process, which had to obtain player data, select and parse a format, apply authentication and HTTP headers, and return a signed URL before `mpv` could connect.

The repository history also records an additional TTMediaBot-specific mitigation for signed `googlevideo.com` URLs that returned 403 when handed to `mpv` immediately after extraction. An intentional playback wait was introduced at 3.2 seconds, tested between 1 and 4 seconds, and stabilized at 2 seconds immediately before the migration. This was an empirical compatibility workaround in the old backend, not a general requirement documented by YouTube or `yt-dlp`. Combined with extraction time, it commonly made a track take roughly 3–4 seconds to begin; if playback or extraction failed and the bot advanced to the next result, the same expensive path was repeated.

Removing that wait while retaining the old backend did not provide an equivalent solution. The repository briefly tested faster Android and `android_vr` clients, but the `android_vr` path deliberately removed the user's cookie file and therefore could not preserve the same authenticated, personalized experience. Content requiring authentication then had to fall back to a second extraction with a cookie-capable client. In practice, the sequential client attempt, failure detection, and authenticated fallback could increase perceived playback startup to roughly 10–15 seconds. The fallback was subsequently removed because of its complexity, leaving the signed, cookie-aware path and its shorter compatibility wait as the better compromise until the YouTube.js migration.

TTMediaBot therefore replaced the per-track `yt-dlp` hot path with a long-running `YouTube.js` service. YouTube.js still performs the required player-script deciphering and PO-token handling; the migration does not bypass or remove YouTube's protections. It instead keeps sessions and player data warm, reuses bounded caches, deduplicates concurrent requests, and resolves streams without spawning a new extractor for every transition or imposing the old artificial playback wait. Detailed timing logs cover search, next-track selection, resolution, handoff to `mpv`, and actual playback start so regressions can be measured instead of inferred.

### One backend for all bots

Earlier YouTube.js builds started a Node.js bridge and PO-token provider inside every bot container. That design isolated instances, but multiplied memory use and startup load as the bot count increased. The current architecture runs both Node.js processes once in the dedicated `ttmediabot-youtube` container:

1. A bot running with host networking sends search or resolve requests to the bridge through the host-only endpoint `http://127.0.0.1:4417`.
2. The request includes a validated bot identifier, which selects only that bot's `bots/<name>/cookies.txt` file.
3. The bridge maintains isolated authenticated sessions per cookie file while sharing bounded public-search caches and deduplicating pending search, recommendation, and resolution requests.
4. The bridge resolves a playable audio stream and the Python bot passes it to `mpv`.
5. If the shared service is restarting, clients retry with bounded exponential backoff.

The bridge is published only on `127.0.0.1:4417`; the PO-token provider remains internal to the shared container. This preserves per-account cookie separation without exposing either service publicly. Up to 64 cookie-backed sessions are retained in RAM with least-recently-used eviction to prevent unbounded growth. This is not a 64-bot limit: additional bots continue to work, and an evicted session is recreated from that bot's on-disk cookie file when needed.

Public catalog searches are cached for 10 minutes (up to 512 normalized queries) and may be shared because they contain no account-private state. Authenticated recommendations remain separated by cookie identity and are cached for 10 minutes with a 256-entry bound. Stream resolutions are also isolated by cookie, client, and video; their lifetime is derived from the signed URL's `expire` value, reduced by a safety margin and capped at one hour. If `mpv` rejects a cached stream, TTMediaBot invalidates both Python and bridge caches, resolves a fresh URL, and retries once.

The shared service can be started, stopped, or restarted independently through main-menu option **8**, without restarting every TeamTalk bot.

### Verified behavior and performance

The unified backend is covered by Node.js tests for bounded TTL/LRU eviction, in-flight request deduplication, media mapping, and signed-URL expiry, plus Python contract tests for bridge calls, YouTube Music migration, stream refresh, and one-shot player recovery. A clean option **3** rebuild runs without `ytmusicapi` in the resulting image and recreates both the shared service and bot containers against the new architecture.

During the post-migration validation, uncached video and Music searches completed in approximately 0.47–0.54 seconds, while equivalent cache hits completed in approximately 3–4 milliseconds. A forced fresh stream resolution completed in approximately 0.37 seconds and the following cache hit in approximately 3 milliseconds. These figures are reference measurements from the validation host, not fixed guarantees; network path, account state, YouTube responses, and host load still affect real latency.

The same validation resolved a 36,107-second video without changing the existing long-media `mpv` settings. Cache rejection recovery remains deliberately limited to one retry: the rejected URL is invalidated in both cache layers, a new signed URL is requested, and normal failure handling resumes if that retry also fails.


## 🎵 YouTube Music Support

This fork includes optimized support for **YouTube Music** alongside regular YouTube:


- **YouTube.js Bridge Integration:** High-performance persistent `YouTube.js` (`youtubei.js`) bridge for fast YouTube search and direct audio stream resolution
- **Unified YouTube.js Backend:** YouTube video search, YouTube Music song search, authenticated Up Next recommendations, and stream resolution all use the persistent shared bridge; the former per-bot `ytmusicapi` client and its HTTP connection pool have been removed
- **Performance Focus & Warmup:** Persistent sessions and background pre-warming reduce first-request latency, while bounded LRU caches accelerate repeated catalog searches, recommendations, and stream resolution
- **Unified Cookie System:** Both YouTube and YouTube Music use the same cookies configuration for authentication
- **📦 Playlist & Album Downloads:** Full support for downloading entire collections via the `dlp` command with metadata-aware naming
- **Complete Playlist Loading:** YouTube playlists and channel URLs use continuation pagination, with loading progress and the final track count reported to the requester
- **🕵️ Real-time PM Progress:** Stay updated on your downloads without cluttering the channel

Switch between services using the `sv` command:
- `sv yt` - Switch to YouTube
- `sv ytm` - Switch to YouTube Music

> [!NOTE]
> **Exclusive Feature:** YouTube Music support is exclusive to this fork and is not available in the original TTMediaBot project.

## 📻 Personalized Autoplay & Recommendations

This fork includes an advanced **Autoplay / Related Videos** system for both YouTube (`yt`) and YouTube Music (`ytm`) services, delivering a continuous music playback experience (similar to YouTube Music's "Radio" or standard YouTube's "Up Next" queue).

### Features
- **🆕 YouTube (`yt`) Implementation from Scratch:** Previously, the standard YouTube service did not support autoplay or recommendations. This feature has been fully implemented from scratch using a watch-page scraper that parses recommendations.
- **🔒 YTM Authenticated & Safe Autoplay:** The shared YouTube.js Music client fetches Up Next recommendations through the requesting bot's authenticated cookie session, while public catalog searches remain safely shareable.
- **🔄 Zero-Interruption Playback:** When playing the last track in the queue, the bot automatically fetches and appends related tracks (5 tracks for Autoplay, or 20 tracks for dynamic queue lists) to keep the music going.
- **🍪 Personalized Recommendations:** Both YouTube (`yt`) and YouTube Music (`ytm`) services fetch autoplay suggestions using the configured account cookies (`cookies.txt`). This ensures your autoplay experience is completely personalized and aligned with your account's listening history instead of pulling generic global lists.
- **🛡️ Robust Autoplay Scraper:** Scrapes both the new YouTube layout structures (`lockupViewModel`) and classic layout structures (`compactVideoRenderer`) recursively from watch pages, parsing recommendations with complete thread safety and deadlock prevention.

## 🔗 Link-Based Downloading & Local Storage

This fork includes an advanced link-based downloading system that allows users to queue media links, list them, manage them, and download them sequentially or in compressed archives.

### Commands
- **`aad [link]`**: Adds a single link to your list.
- **`ad [link1] [link2] ...`**: Adds multiple space-separated links to your list.
- **`ld`**: Lists all links currently in your list.
- **`rd [number/link]`**: Removes a link from your list by index or URL.
- **`ldd [link]`**: Downloads a link directly and uploads it to the channel.
- **`ads`**: Downloads your list. Prompts you to select:
  - **Option 1 (Normal):** Downloads each track individually and uploads it to the channel.
  - **Option 2 (ZIP):** Resolves and compresses all tracks into a single ZIP archive, then uploads it to the channel.
- **`adsc`**: Toggles **local download mode** (volatile). When enabled:
  - Tracks from the `ads` list are stored directly on the VPS filesystem instead of uploaded to TeamTalk.
  - Option 1 stores files under `data/Downloads/music/` (host: `bots/nomedobot/Downloads/music/`).
  - Option 2 stores ZIP archives under `data/Downloads/zips/` (host: `bots/nomedobot/Downloads/zips/`).
  - Files saved locally are never deleted automatically.
  - Displays a final success/error report upon completion.

## 🚀 Easy Installation (Recommended)

`install_git_clone.sh` is the recommended entry point. It acquires root privileges when necessary, detects the available Linux package manager, installs Git and extraction tools, clones or updates the repository, detects `x86_64` or ARM, downloads the matching TeamTalk SDK library, and launches the Docker manager. The manager then installs Docker and `jq` when required, builds the image, and creates the shared YouTube service.

1.  **Download and run the installer:**
    ```bash
    wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/install_git_clone.sh
    sudo chmod +x install_git_clone.sh
    sudo ./install_git_clone.sh
    ```

2.  **Monitor the terminal:**
    *   The script will automatically install all dependencies (including Docker if needed).
    *   Keep an eye on the terminal output to track the installation progress.
    *   You can manage multiple bots, update code, and change configurations through the Docker manager.

### Alternative local installer

`install.sh` installs the Python virtual environment, Node.js dependencies, FFmpeg, TeamTalk libraries, and project requirements directly on a supported Linux host. It is intended for manual/non-Docker deployments and development. For normal multi-bot operation, prefer `install_git_clone.sh` and `ttbotdocker.sh`, because the Docker workflow also manages service health, upgrades, container recreation, architecture-specific libraries, and cleanup.

---

## ⚙️ Manual Configuration

If you need to manually edit bot configurations after setup:

1. **Configuration files** are located in the `bots` directory inside the `TTMediaBot` folder after initial setup
2. **Make your changes** to the configuration files as needed
3. **Restart the bot** using one of these methods:
   - **Via Docker script:** Run `./ttbotdocker.sh`, select option `2` (Manage Bots), then choose the restart option (usually option `2`)
   - **Via bot command:** Send `rs` as a private message to the bot (requires admin privileges)

---

## 🎮 Commands

Send these commands to the bot via private message (PM) or in the channel (if enabled).

### User Commands
| Command | Arguments | Description |
| :--- | :--- | :--- |
| **h** | | Shows command help. |
| **p** | `[query]` | Plays tracks found for query. If no query, pauses/resumes. |
| **u** | `[url]` | Plays a stream/file from a direct URL. |
| **s** | | Stops playback. |
| **n** | `[number/?]` | Plays the next track, jumps to a positive or negative track index, or reports the current position with `?`. |
| **b** | | Plays the previous track. |
| **v** | `[0-100]` | Sets volume. No arg shows current volume. |
| **sb** | `[seconds]` | Seeks backward. Default step if no arg. |
| **sf** | `[seconds]` | Seeks forward. Default step if no arg. |
| **c** | `[number/?]` | Selects a positive or negative track index; without an argument or with `?`, reports the current position. |
| **m** | `[mode]` | Sets playback mode: `SingleTrack`, `RepeatTrack`, `TrackList`, `RepeatTrackList`, `Random`. |
| **sp** | `[0.25-4]` | Sets playback speed. |
| **sv** | `[service]` | Switches service (e.g., `sv yt`, `sv ytm`). |
| **f** | `[+/-][num]` | Favorites management. `f` lists. `f +` adds current. `f -` removes. `f [num]` plays. |
| **gl** | | Gets a direct link to the current track. |
| **dl** | | Downloads current track and uploads to channel. |
| **dlv** | | Downloads current track as video and uploads it to channel. |
| **dlp** | `[url]` | Downloads all tracks from a playlist/album URL, zips them, and uploads to the channel. |
| **aad** | `[link]` | Adds a single link/URL to your custom download list. |
| **ad** | `[links]` | Adds multiple space-separated links to the download list. |
| **ld** | | Lists all links currently in the download list. |
| **rd** | `[number/link]` | Removes a link from the download list by its index or URL. |
| **ldd** | `[link]` | Downloads a link directly and uploads to the TeamTalk channel. |
| **ads** | `[1/2]` | Downloads list: Option 1 (Normal sequentially) or Option 2 (ZIP compressed). |
| **adsc** | | Toggles local download mode: saves files locally to the VPS instead of uploading. |
| **r** | `[number]` | Plays from Recents. `r` lists recents. |
| **jc** | | Makes the bot join your current channel. |
| **qa** | `[query]` | Adds a track to the queue. |
| **ql** | | Lists all tracks currently in the queue. |
| **qr** | `[number]` | Removes a specific track from the queue. |
| **qc** | | Clears the entire queue. |
| **qs** | | Skips current track and plays the next one from the queue. |
| **sr** | `[on/off]` | Toggles Search Results Mode. When active, `p QUERY` shows a numbered list instead of playing immediately. Save with `sc`. |
| **sl** | `[number]` | Selects and plays result NUMBER from the last `sr` search list. |
| **slc** | `[number]` | Sets how many results are shown in `sr` mode. The volatile count defaults to 1 after every restart; no argument shows the current count. |
| **a** | | Shows about info. |

### Admin Commands
*Requires admin privileges defined in `config.json`.*

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **cg** | `[n/m/f]` | Changes bot gender. |
| **cl** | `[code]` | Changes language (e.g., `en`, `ru`, `pt_BR`). |
| **cn** | `[name]` | Changes bot nickname. |
| **cs** | `[text]` | Changes bot status text. |
| **cc** | `[r/f]` | Clears cache (`r`=recents, `f`=favorites). |
| **cm** | | Toggles sending channel messages. |
| **ajc** | `[id] [pass]` | Force join channel by ID. |
| **bc** | `[+/-cmd]` | Blocks/Unblocks a command. |
| **l** | | Locks/Unlocks the bot (only admins can use it). |
| **ua** | `[+/-user]` | Adds/Removes admin users. |
| **ub** | `[+/-user]` | Adds/Removes banned users. |
| **eh** | | Toggles internal event handling. |
| **sc** | | Saves current configuration to file. |
| **va** | | Toggles voice transmission. |
| **rs** | | Restarts the bot. |
| **q** | | Quits the bot. |
| **gcid** | | Gets the current channel ID. |

---

## 🐳 Docker Management Script (`ttbotdocker.sh`)

The `ttbotdocker.sh` script is a comprehensive management tool for TTMediaBot. It provides a menu-driven interface to handle all aspects of bot deployment and management.

### Main Menu Options

#### 1. Create Bot
Creates a new bot instance with full configuration wizard:
- **Bot naming:** Container and folder name
- **Server configuration:** Hostname, TCP/UDP ports, encryption
- **Credentials:** Username and password
- **Cookies:** Path to YouTube cookies file
- **Batch creation:** Create multiple bots at once with automatic numbering
  - Automatically detects existing bot numbers and continues sequence
  - Separate naming for containers and nicknames
  - Prevents conflicts on the same TeamTalk server

#### 2. Manage Bots
Comprehensive bot management submenu with 13 options:

**2.1. Start All Bots**
- Starts all stopped bot containers
- Uses Docker label filtering (`role=ttmediabot`)

**2.2. Restart All Bots**
- Stops all bots (1 second timeout)
- Immediately starts them again
- Useful for applying configuration changes

**2.3. Stop All Bots**
- Gracefully stops all running bots
- 1 second timeout for clean shutdown

**2.4. Delete Bot**
- Interactive menu to select and delete a single bot
- Shows numbered list of all bots
- Removes both container and configuration folder
- Requires confirmation before deletion

**2.5. Bulk Delete Bots**
- Delete multiple bots in one operation
- Enter space-separated numbers (e.g., `1 3 5`)
- Use option `0` to **delete ALL bots** simultaneously
- Shows summary before deletion
- Efficient parallel container removal

**2.6. Duplicate Bot**
- Clone an existing bot's configuration
- Select source bot from numbered list
- Shows server address for each bot
- Batch duplication support (create multiple copies)
- Automatic numbering for containers and explicitly asks for **NICKNAME BASE**
- Smart conflict detection: prevents cloning if the chosen base name already exists

**2.7. Update Cookies (All Bots)**
- Update YouTube cookies for all bots at once
- Copies new cookies file to all bot directories
- Automatically restarts all bots to apply changes
- Sets correct file permissions (1000:1000)

**2.8. Restart with Timer**
- Stops all bots, waits specified time, then starts them
- Useful for coordinated server maintenance
- Visual countdown timer
- Time specified in seconds

**2.9. Bulk Update Configuration**
- Update configuration for all bots simultaneously
- Choose what to update:
  1. Server (hostname)
  2. Ports (TCP/UDP)
  3. Encryption
  4. Credentials (username/password)
  5. Everything
- Shows current configuration from first bot
- Preview changes before applying
- Updates all bot `config.json` files

> [!WARNING]
> **Important:** This feature is designed for bots on the **same server**. If you have bots connected to multiple different TeamTalk servers, you'll need to update them manually. Using this feature will configure all bots with the same server settings.

**2.10. Backup / Restore Bots**
- Portable backup/restore utility for bots config and cache.
- Saves compressed backups (`.tar.gz`) to a `backups/` directory.
- Restoring dynamically redeploys bot configurations and recreates Docker containers.

**2.11. Clear All Bot Logs**
- Quick-clear utility that deletes all `*.log` files from all bot data folders to free up disk space.

**2.12. Clear All Bot Caches**
- Deletes `*.cache` and `*.dat` cache files only from bot directories under `bots/`.
- Preserves bot configuration, cookies, downloads, logs, and files outside the managed bot directory.
- Requires explicit confirmation before cleanup.

**2.13. Return to Main Menu**

#### 3. Rebuild Image / Update Code
Updates the bot code and rebuilds the Docker image:
- Pulls the current base image and uses `CACHEBUST` before dependency installation to refresh system packages, the token provider, YouTube.js, and Python packages. Explicit rebuilds take longer because dependency layers are refreshed.
- Recreates containers with new image
- Restarts only previously running bots

#### 4. Uninstall Menu
Launches a dedicated uninstallation submenu (`uninstall.sh`) offering two distinct options:

- **Option 1: Standard Uninstall (Safe & Recommended)**
  - Removes ONLY TTMediaBot containers, the `ttmediabot` Docker image, bot data directories (`bots/`), auto-updater service, and temp files.
  - **Preserves** Docker Engine, system packages (`git`, `curl`, `jq`), and any other Docker projects on the machine.

- **Option 2: Full System Purge (DESTRUCTIVE)**
  - Complete cleanup of TTMediaBot, Docker Engine, Docker volumes, networks, iptables rules, and system packages (`git`, `curl`, `jq`, `gnupg`).
  
  > [!CAUTION]
  > **Legal Disclaimer & Warning:**
  > The developer/author assumes **NO RESPONSIBILITY OR LIABILITY** for any damage, data loss, system instability, or downtime caused by executing the Full System Purge option. Do **NOT** run Option 2 on a production server or a shared server running other critical services or containers!

#### 5. Check for Updates
Automatically checks the GitHub repository for updates.
- Uses `update.sh` to compare local code with the remote repository
- Safely backups configuration before updating
- Includes a pause at the end so users can read the console

#### 6. Enable/Disable Auto-Updates
Dedicated menu to toggle background updates via systemd masking.

#### 7. Clean Docker Cache (Unused)
Advanced cleanup tool to reclaim disk space without affecting running bots:
- **Docker Prune:** Removes stopped containers and unused images.
- **Buildx Cleanup:** Wipes persistent build caches.
- **System Logs:** Vacuums `journalctl` logs older than 1 day.
- **Zero-Footprint:** Ensures the host system stays lean.

> [!CAUTION]
> This is a host-wide Docker cleanup, not a TTMediaBot-only cleanup. Unused containers, images, volumes, and build caches belonging to other Docker projects may also be removed. Running containers are not removed.

#### 8. Manage Shared YouTube Servers
Launches `youtube_server_manager.sh` to control the shared YouTube backend independently:
- **Start Servers:** Starts `ttmediabot-youtube` and waits for the bridge health check.
- **Stop Servers:** Stops the shared bridge and PO-token provider container without stopping bot containers.
- **Restart Servers:** Restarts the shared service and verifies that it becomes healthy again.
- **Return:** Goes back to the main manager.

#### 9. Exit
Closes the script

### Automatic Features

The script automatically:
- **Checks for Updates** automatically on startup if `update.sh` is present
- **Installs dependencies** (Docker, jq) on first run
- **Builds Docker image** automatically and forces PIP to update libraries (`-U`) on every rebuild
- **Creates and health-checks the shared YouTube service** before starting or recreating bots
- **Migrates legacy per-bot bridge containers** to the current shared-service layout during rebuilds and updates
- **No startup prompts:** Rebuilding is now a manual menu option (Option 3), making startup faster
- **Creates `bots` directory** structure
- **Detects conflicts** (container names, nicknames on same server)
- **Sets permissions** correctly for Docker volumes
- **Uses labels** for easy container filtering

---

## 🔄 Standalone Update Script (`update.sh`)

If you already have bots installed and just want to update the code without using the full Docker manager, you can use the standalone `update.sh` script.

**How to use:**
1. Download the script to your `TTMediaBot` folder:
   ```bash
   wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/update.sh
   chmod +x update.sh
   ```
2. Run it:
   ```bash
   sudo ./update.sh
   ```

This script backs up bot data, synchronizes the repository, selects the correct TeamTalk SDK library for the host architecture, rebuilds the image, recreates the shared YouTube service, health-checks it, and then recreates the bot containers while preserving their previous running/stopped state. Its cleanup is scoped to TTMediaBot resources and conservative Docker pruning.

### 📢 Early Warning Update System

This fork features an **Early Warning Update System** designed to notify users in the TeamTalk channels when an update starts.

* **How it works:** 
  1. **Pre-Update Alert:** As soon as you run `update.sh` (or when `auto_updater.sh` runs automatically in the background) and confirm the update (by selecting `y`), the script sends an update signal to all active bot containers. The bots instantly check this signal and post a localized message in the active TeamTalk channel: 
     > *“The bot is starting an update process and will restart shortly. It may go offline at any moment.”*
     This is posted **immediately when the Docker build starts**, giving users a 1-to-2 minute heads-up while the image compiles in the background.
  2. **Graceful Shutdown Alert:** When the container receives the shutdown signal (`SIGTERM`) from Docker to restart or stop, it captures the signal and immediately posts a final localized notification to the active channel:
     > *“The bot is restarting now to apply the update. See you in a moment!”*
     This ensures users know exactly when the bot is going offline.
  3. **Update Success Alert:** Once `update.sh` finishes restarting the Docker containers, it leaves a success marker. Upon booting back up, the bot detects this marker, posts a localized message:
     > *“Update completed successfully! I am back online.”*
     And deletes the marker, confirming to users that the bot is fully updated and operational.
* **Localization:** All warning and success messages automatically adapt to each bot's configured language. They are fully translated into all 8 supported languages (English, Portuguese, Spanish, Russian, Turkish, Arabic, Hungarian, Indonesian).

---

## 🍪 YouTube & YouTube Music Cookies Configuration

Cookies are **essential** for the bot to play music from both **YouTube** and **YouTube Music** due to platform restrictions.

### Why Cookies Are Needed

YouTube and YouTube Music have implemented restrictions that require authentication to access certain content. Cookies from an authenticated browser session allow the bot to bypass these restrictions and play music from both services.

### How to Obtain Cookies

1. **Login to your Google account** in your browser (Chrome, Edge, or Firefox)

2. **Install the Get cookies.txt extension:**
   - Chrome/Edge: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

3. **Navigate to YouTube:** Go to `youtube.com`

4. **Export cookies:**
   - Click on the **Extensions menu** in your browser
   - Click on the **Get cookies.txt LOCALLY** extension icon
   - Click **"Export All Cookies"**
   - Click the **Download button**
   - Your browser may ask where to save the file - choose a location you can access
   - If not prompted, the file will be in your **Downloads** folder

5. **Place the file** in an accessible location on your server (e.g., `/root/cookies.txt`)

### Getting the Cookies File Path

When creating or updating bots, the script will ask for the **full path** to your cookies file. If you uploaded the file to your server, use this command to get the absolute path:

**Example: If you're in the directory where you uploaded cookies.txt**

```bash
# Navigate to the directory containing cookies.txt
cd /path/to/your/directory

# Get the full path
pwd
# Output: /root/my-cookies

# Or get the full path directly
realpath cookies.txt
# Output: /root/my-cookies/cookies.txt
```

**Quick command to get the path:**
```bash
echo "$(pwd)/cookies.txt"
# Output: /root/my-cookies/cookies.txt
```

Copy this full path and paste it when the bot creation or update script asks for the cookies file location.

> [!IMPORTANT]
> **Note:** The YouTube.js bridge reads Netscape-format `cookies.txt` files and forwards only YouTube/Google cookies to the Innertube session. Keep the cookie file limited to the required YouTube/Google domains.

### Updating Expired Cookies

Cookies expire periodically. When YouTube playback stops working:

1. **Generate new cookies** following the steps above
2. **Update all bots** using the Docker script:
   - Run `./ttbotdocker.sh`
   - Select option `2` (Manage Bots)
   - Select option `7` (Update Cookies - All Bots)
   - Enter the path to your new cookies file
   - The script will automatically update and restart all bots

### Manual Cookie Update

Alternatively, update cookies manually:
1. Copy new `cookies.txt` to each bot folder in `bots/[bot_name]/`
2. Restart the affected bot(s)

---

## 🌍 Supported Languages

TTMediaBot supports multiple languages. Change language using the `cl` admin command.

**Available languages:**
- `ar` - Arabic
- `en` - English
- `es` - Spanish
- `hu` - Hungarian
- `id` - Indonesian
- `pt_BR` - Brazilian Portuguese
- `ru` - Russian
- `tr` - Turkish

**Example:** Send `cl pt_BR` to switch to Brazilian Portuguese.

---

## 🔧 Troubleshooting

### Bot Not Playing YouTube Music

**Symptoms:** Bot connects but YouTube or YouTube Music tracks do not start

**Solutions:**
1. **Check cookies:**
   - Cookies may have expired
   - Generate new cookies and update (see YouTube Cookies section)
   - Verify cookies file path in `config.json`

2. **Verify cookies file exists:**
   ```bash
   ls -la bots/[bot_name]/cookies.txt
   ```

3. **Check bot logs:**
   - **Docker logs:**
     ```bash
     docker logs [bot_name]
     ```
   - **Log file:** Check `bots/[bot_name]/TTMediaBot.log` directly.

4. **Check the shared YouTube service:**
   ```bash
   curl -fsS http://127.0.0.1:4417/health
   docker logs --tail 100 ttmediabot-youtube
   ```
   You can also use option `8` in `ttbotdocker.sh` to restart the shared servers without restarting the bots.

### Bot Won't Connect to Server

**Symptoms:** Bot doesn't appear online

**Solutions:**
1. **Verify server details:**
   - Check hostname, ports in `config.json`
   - Test server connectivity: `ping [hostname]`

2. **Check credentials:**
   - Verify username/password are correct
   - Ensure bot account exists on TeamTalk server

3. **Check encryption setting:**
   - If server uses encryption, set `"encrypted": true` in config.
   - **Note:** The bot automatically fetches and trusts the server's SSL certificate dynamically (similar to the Windows client) if no local CA certificate (`ttservercert.pem`) is provided.

4. **View logs:**
   - **Docker:** `docker logs [bot_name]`
   - **File:** `bots/[bot_name]/TTMediaBot.log`

### Audio Issues / No Sound

**Symptoms:** Bot connects but no audio output

**Solutions:**
1. **Check PulseAudio:**
   - PulseAudio runs inside the container
   - Restart the bot: `docker restart [bot_name]`

2. **Check volume:**
   - Send `v` command to check current volume
   - Set volume: `v 50`

3. **Verify audio device configuration:**
   - Check `sound_devices` section in `config.json`

### Container Won't Start

**Symptoms:** Docker container exits immediately

**Solutions:**
1. **Check logs:**
   - **Docker:** `docker logs [bot_name]`
   - **File:** `bots/[bot_name]/TTMediaBot.log`

2. **Verify configuration:**
   - Ensure `config.json` is valid JSON
   - Check for syntax errors

3. **Recreate container:**
   - Delete and recreate the bot using `ttbotdocker.sh`

### Permission Errors

**Symptoms:** Bot can't read/write files

**Solutions:**
1. **Fix permissions:**
   ```bash
   sudo chown -R 1000:1000 bots/[bot_name]
   ```

2. **Run script as root:**
   - Always use `sudo ./ttbotdocker.sh`

---

## ❓ FAQ (Frequently Asked Questions)

### Q: Can I run multiple bots on the same server?
**A:** Yes! The bot supports multiple instances. Use the batch creation feature in `ttbotdocker.sh` or create bots individually. Each bot gets its own container and configuration.

### Q: How do I add more administrators?
**A:** Two ways:
- **Via command:** Send `ua +username` to the bot (requires existing admin privileges)
- **Via config:** Edit `bots/[bot_name]/config.json`, add username to `teamtalk.users.admins` array, then restart

### Q: How do I backup my bot configurations?
**A:** Simply copy the entire `bots` directory:
```bash
cp -r bots bots_backup_$(date +%Y%m%d)
```

### Q: Can I use the same cookies for all bots?
**A:** Yes. Use "Update Cookies (All Bots)" in the management menu to apply one cookies file to every bot. The bridge still creates a separately keyed session for each bot/cookie file, so requests do not accidentally select another bot's cookie path.

### Q: The bot keeps disconnecting. What should I do?
**A:** Check:
- Network stability
- Server status
- Bot logs: `docker logs [bot_name]` or check `bots/[bot_name]/TTMediaBot.log`
- Increase `reconnection_timeout` in `config.json`

### Q: How do I change the bot's nickname?
**A:** Two ways:
- **Via command:** Send `cn NewNickname` (admin only)
- **Via config:** Edit `teamtalk.nickname` in `config.json`, then restart

### Q: Can I run bots on different TeamTalk servers?
**A:** Absolutely! Each bot can connect to a different server. Just specify different hostnames during creation or in the configuration.

### Q: How much resources does each bot use?
**A:** Resource use depends on active playback, downloads, FFmpeg transcoding, and TeamTalk traffic. Bot containers share the same Docker image layers and one `ttmediabot-youtube` backend, so Node.js and image dependencies are not duplicated per bot. Each bot adds its Python/TeamTalk process, runtime memory, configuration, cache, logs, and downloaded files. Use `docker stats` for measurements on your host.

### Q: What happens if I update the repository code?
**A:** Bot configurations in `bots/` are preserved. Use option `3` in `ttbotdocker.sh` for a manual rebuild or run `update.sh`; the supported workflow backs up bot data, synchronizes the repository, rebuilds the image, recreates and health-checks the shared YouTube service, then recreates bot containers while preserving their previous running/stopped state.

---

---

## 📊 Logs and Monitoring

### Viewing Real-Time Logs

**For a specific bot:**
```bash
docker logs -f [bot_name]
```

**For all bots:**
```bash
for bot in $(docker ps --format '{{.Names}}' -f "label=role=ttmediabot"); do
    echo "===== $bot ====="
    docker logs --tail 100 "$bot"
done
```

**For the shared YouTube bridge and PO-token provider:**
```bash
docker logs -f ttmediabot-youtube
```

### Log Files Location

Each bot stores logs in its directory:
```
bots/[bot_name]/TTMediaBot.log
```

### Log Configuration

Edit log settings in `config.json`:

```json
"logger": {
    "log": true,
    "level": "INFO",
    "format": "%(levelname)s [%(asctime)s]: %(message)s",
    "mode": "FILE",
    "file_name": "TTMediaBot.log",
    "max_file_size": 0,
    "backup_count": 0
}
```

**Log levels:**
- `DEBUG` - Detailed information for diagnosing problems
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

**Enable debug logging:**
Change `"level": "INFO"` to `"level": "DEBUG"` and restart the bot.

### Monitoring Bot Status

**Check running bots:**
```bash
docker ps -f "label=role=ttmediabot"
```

**Check all bots (including stopped):**
```bash
docker ps -a -f "label=role=ttmediabot"
```

**Check resource usage:**
```bash
docker stats $(docker ps -q -f "label=role=ttmediabot") ttmediabot-youtube
```

### Playback Latency Diagnostics

Search the bot log for `[PlaybackTiming]` to follow one request through command handling, search, task-queue wait, stream resolution, `mpv` loading, and playback start:

```bash
grep '\[PlaybackTiming\]' bots/[bot_name]/TTMediaBot.log
```

Bridge-side cache hits, misses, pending-resolution joins, selected clients, and resolution time are written to `docker logs ttmediabot-youtube`. Comparing both logs separates TeamTalk command latency, queue pressure, YouTube resolution time, and `mpv` startup time.

---

## ⚖️ Legal Disclaimer & Terms of Use

This software and associated scripts are provided "AS IS", without warranty of any kind, express or implied.

- **No Liability:** The developer/author assumes **absolutely no responsibility or liability** for any direct, indirect, incidental, or consequential damages, data loss, server downtime, system instability, or hardware/software failures resulting from the use or execution of this repository, scripts (`ttbotdocker.sh`, `uninstall.sh`, `install.sh`), or bot commands.
- **Production Warning:** Using the Full System Purge option or automated scripts on production servers or shared environments is done **at your own risk**. Ensure you have proper backups before executing systemic changes.
