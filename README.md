# TTMediaBot

> **Note:** This repository is a fork of the [original TTMediaBot](https://github.com/gumerov-amir/TTMediaBot).

A feature-rich media streaming bot for TeamTalk 5, capable of playing music from various services (YouTube, YouTube Music, local files, URLs) with advanced control features.

## 📋 Changes from Original

This fork includes several modifications and optimizations:

- **Removed Services:** Yandex Music and VK integration have been removed
- **TeamTalk SDK Upgrade:** Updated to TeamTalk SDK 5.8.1 for improved performance
- **Docker Containerization:** The bot runs in Docker containers based on Debian 11 and Python 3.10, ensuring compatibility with legacy dependencies while maintaining stability
- **Proven Stability:** Since I first encountered this bot in 2021, the adaptations made to work around YouTube's restrictions, combined with the optimizations from 2021/2022, have proven to be excellent and reliable

## 🚀 Easy Installation (Recommended)

This script will automatically install Git (if needed), clone the repository, and set up the Docker environment.

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

---

## ⚙️ Manual Configuration

If you need to manually edit bot configurations after setup:

1. **Configuration files** are located in the `bots` directory after initial setup
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
| **n** | | Plays the next track. |
| **b** | | Plays the previous track. |
| **v** | `[0-100]` | Sets volume. No arg shows current volume. |
| **sb** | `[seconds]` | Seeks backward. Default step if no arg. |
| **sf** | `[seconds]` | Seeks forward. Default step if no arg. |
| **c** | `[number]` | Selects a track by number from search results. |
| **m** | `[mode]` | Sets playback mode: `SingleTrack`, `RepeatTrack`, `TrackList`, `RepeatTrackList`, `Random`. |
| **sp** | `[0.25-4]` | Sets playback speed. |
| **sv** | `[service]` | Switches service (e.g., `sv yt`, `sv ytm`). |
| **f** | `[+/-][num]` | Favorites management. `f` lists. `f +` adds current. `f -` removes. `f [num]` plays. |
| **gl** | | Gets a direct link to the current track. |
| **dl** | | Downloads current track and uploads to channel. |
| **r** | `[number]` | Plays from Recents. `r` lists recents. |
| **jc** | | Makes the bot join your current channel. |
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
Comprehensive bot management submenu with 10 options:

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
- Shows summary before deletion
- Efficient parallel container removal

**2.6. Duplicate Bot**
- Clone an existing bot's configuration
- Select source bot from numbered list
- Shows server address for each bot
- Batch duplication support (create multiple copies)
- Automatic numbering for containers and nicknames
- Smart conflict detection (only checks same server)

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

**2.10. Return to Main Menu**

#### 3. Uninstall Everything
Complete cleanup of TTMediaBot installation:
- Stops all bot containers
- Removes all containers
- Deletes all bot folders
- Removes Docker image
- **Warning:** This is irreversible!

#### 4. Exit
Closes the script

### Automatic Features

The script automatically:
- **Installs dependencies** (Docker, jq) on first run
- **Builds Docker image** if not present
- **Creates `bots` directory** structure
- **Detects conflicts** (container names, nicknames on same server)
- **Sets permissions** correctly for Docker volumes
- **Uses labels** for easy container filtering

---

## 🍪 YouTube Cookies Configuration

YouTube cookies are **essential** for the bot to play music from YouTube due to platform restrictions.

### Why Cookies Are Needed

YouTube has implemented restrictions that require authentication to access certain content. Cookies from an authenticated browser session allow the bot to bypass these restrictions.

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

> [!IMPORTANT]
> **Note:** Do not use very large cookie files. If the cookies file is too large, yt-dlp may not recognize it and the bot won't play music. Use cookies only from YouTube/Google domains.

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
- `en` - English
- `es` - Spanish (Español)
- `hu` - Hungarian (Magyar)
- `id` - Indonesian (Bahasa Indonesia)
- `pt_BR` - Brazilian Portuguese (Português Brasileiro)
- `ru` - Russian (Русский)
- `tr` - Turkish (Türkçe)

**Example:** Send `cl pt_BR` to switch to Brazilian Portuguese.

---

## 🔧 Troubleshooting

### Bot Not Playing YouTube Music

**Symptoms:** Bot connects but won't play YouTube tracks

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
   ```bash
   docker logs [bot_name]
   ```

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
   - If server uses encryption, set `"encrypted": true` in config

4. **View container logs:**
   ```bash
   docker logs [bot_name]
   ```

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
   ```bash
   docker logs [bot_name]
   ```

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
**A:** Yes! Use the "Update Cookies (All Bots)" feature in the management menu to apply the same cookies file to all bots at once.

### Q: The bot keeps disconnecting. What should I do?
**A:** Check:
- Network stability
- Server status
- Bot logs: `docker logs [bot_name]`
- Increase `reconnection_timeout` in `config.json`

### Q: How do I change the bot's nickname?
**A:** Two ways:
- **Via command:** Send `cn NewNickname` (admin only)
- **Via config:** Edit `teamtalk.nickname` in `config.json`, then restart

### Q: Can I run bots on different TeamTalk servers?
**A:** Absolutely! Each bot can connect to a different server. Just specify different hostnames during creation or in the configuration.

### Q: How much resources does each bot use?
**A:** Each bot container uses approximately:
- **RAM:** 100-200 MB (idle), 200-400 MB (playing)
- **CPU:** Minimal when idle, moderate when transcoding audio
- **Disk:** ~500 MB per bot (including dependencies)

### Q: What happens if I update the repository code?
**A:** Your bot configurations in the `bots` directory are preserved. After pulling updates:
1. Rebuild the Docker image: `docker build -t ttmediabot .`
2. Recreate containers using the script's recreate function

---

## 📊 Logs and Monitoring

### Viewing Real-Time Logs

**For a specific bot:**
```bash
docker logs -f [bot_name]
```

**For all bots:**
```bash
docker logs -f $(docker ps -q -f "label=role=ttmediabot")
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
docker stats $(docker ps -q -f "label=role=ttmediabot")
```

