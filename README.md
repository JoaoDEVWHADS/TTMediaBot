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

This script will install Git (if needed), clone the repository, and automatically launch the Docker manager to complete the installation.

1.  **Download and run the installer:**
    ```bash
    wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/install_git_clone.sh
    sudo chmod +x install_git_clone.sh
    sudo ./install_git_clone.sh
    ```

2.  **Follow the on-screen menu:**
    *   Select **Install Dependencies** (if you don't have Docker).
    *   The script will then guide you through creating your first bot.
    *   You can manage multiple bots, update code, and change configurations all from within this menu.

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


