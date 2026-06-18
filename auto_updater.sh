#!/bin/bash
# TTMediaBot Auto-Updater Watcher
# This script polls GitHub every 20 seconds and runs update.sh if a new commit is detected.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define SUDO dynamically: use sudo if not root
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

# Fix git safe directory issue when running as root on a repository owned by another user (common in VPS)
git config --global --add safe.directory "$SCRIPT_DIR" 2>/dev/null
git config core.fileMode false 2>/dev/null

# Discover real user and set SSH key command dynamically for root (so we can authenticate with user's key)
REAL_USER=$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null || echo "admin")
REAL_USER_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6 || echo "/home/$REAL_USER")
if [ -f "$REAL_USER_HOME/.ssh/id_ed25519" ]; then
    export GIT_SSH_COMMAND="ssh -i $REAL_USER_HOME/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new"
fi

echo "TTMediaBot Auto-Updater started. Checking every 20 seconds..."

LOCK_FILE="/tmp/ttmediabot_update.lock"

# Cleanup function
cleanup() {
    echo "$(date): Auto-Updater shutting down..."
    $SUDO rm -f "$LOCK_FILE"
    # Kill background sleep if running so we exit immediately
    [ -n "$SLEEP_PID" ] && kill "$SLEEP_PID" 2>/dev/null
    exit 0
}

# Trap signals for clean shutdown (fixes systemd SIGTERM timeout)
trap cleanup INT TERM

# Initial cleanup of stale lock if script is starting fresh
# (Wait 2 seconds to ensure no other instance is starting)
sleep 2
$SUDO rm -f "$LOCK_FILE"

# Function to check if local is behind remote
# Note: we only compare hashes. git ls-remote doesn't download objects,
# so git merge-base would fail with 'Not a valid commit name'.
is_behind_remote() {
    local local_h=$1
    local remote_h=$2
    if [ "$local_h" == "$remote_h" ]; then return 1; fi
    # Hashes differ = remote has changed = we need to update
    return 0
}

while true; do
    # 0. Check for version lock (pin)
    if [ -f "$SCRIPT_DIR/.no_update" ]; then
        # Disallow auto-update if file exists
        sleep 60
        continue
    fi
    # Get current branch name
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "master")
    
    # Check remote hash using ls-remote (no rate limits, no object download)
    REMOTE_HASH=$(git ls-remote origin -h "refs/heads/$BRANCH" 2>/dev/null | awk '{print $1}' | tr -d '[:space:]')
    LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null | tr -d '[:space:]')
    
    # Check what version is currently running in Docker
    RUNNING_HASH=$($SUDO docker inspect ttmediabot --format '{{ index .Config.Labels "commit_hash" }}' 2>/dev/null | tr -d '[:space:]')
    if [ -z "$RUNNING_HASH" ] || [ "$RUNNING_HASH" = "<novalue>" ] || [ "$RUNNING_HASH" = "<noopt>" ] || [[ "$RUNNING_HASH" == *"<no"* ]]; then
        RUNNING_HASH="none"
    fi

    # 1. Update Detection Logic
    SHOULD_UPDATE=false
    
    if [ -n "$REMOTE_HASH" ]; then
        if is_behind_remote "$LOCAL_HASH" "$REMOTE_HASH"; then
            echo "$(date): New version detected on GitHub ($REMOTE_HASH). Triggering update..."
            SHOULD_UPDATE=true
        elif [ "$LOCAL_HASH" != "$RUNNING_HASH" ]; then
            echo "$(date): Local code ($LOCAL_HASH) does not match running image ($RUNNING_HASH). Syncing..."
            SHOULD_UPDATE=true
        fi
    fi

    if [ "$SHOULD_UPDATE" = true ]; then
        if [ -f "$LOCK_FILE" ]; then
            echo "$(date): Update already in progress. Skipping cycle..."
        else
            $SUDO touch "$LOCK_FILE"
            echo "$(date): Running update.sh..."
            HASH_BEFORE=$(git rev-parse HEAD 2>/dev/null)
            export AUTO_UPDATE=true
            $SUDO "$SCRIPT_DIR"/update.sh
            UPDATE_EXIT=$?
            unset AUTO_UPDATE
            $SUDO rm -f "$LOCK_FILE"
            HASH_AFTER=$(git rev-parse HEAD 2>/dev/null)
            echo "$(date): update.sh finished with exit code $UPDATE_EXIT"
            # CRITICAL: update.sh does 'git reset --hard' which replaces THIS script
            # on disk. We must re-exec to pick up the new version, otherwise systemd
            # detects 'command vanished from unit file' and kills us.
            # Only exec if code actually changed to avoid infinite loop.
            if [ "$HASH_BEFORE" != "$HASH_AFTER" ]; then
                echo "$(date): Code updated ($HASH_BEFORE -> $HASH_AFTER). Re-launching..."
                exec "$SCRIPT_DIR/auto_updater.sh"
            fi
        fi
    fi
    # Interruptible sleep: runs in background so SIGTERM can stop us immediately
    sleep 20 &
    SLEEP_PID=$!
    wait "$SLEEP_PID" 2>/dev/null
    SLEEP_PID=""
done
