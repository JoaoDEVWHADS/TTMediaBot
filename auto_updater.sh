#!/bin/bash
# TTMediaBot Auto-Updater Watcher
# This script polls GitHub every 20 seconds and runs update.sh if a new commit is detected.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "TTMediaBot Auto-Updater started. Checking every 20 seconds..."

LOCK_FILE="/tmp/ttmediabot_update.lock"

# Cleanup function
cleanup() {
    echo "Cleaning up lock file..."
    rm -f "$LOCK_FILE"
}

# Trap signals for cleanup
trap cleanup EXIT INT TERM

# Initial cleanup of stale lock if script is starting fresh
# (Wait 2 seconds to ensure no other instance is starting)
sleep 2
rm -f "$LOCK_FILE"

# Function to check if local is behind remote
is_behind_remote() {
    local branch=$1
    local local_h=$2
    local remote_h=$3
    if [ "$local_h" == "$remote_h" ]; then return 1; fi
    if git merge-base --is-ancestor "$local_h" "$remote_h"; then
        return 0
    fi
    return 1
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
    
    # Check remote hash using ls-remote (bypass rate limits)
    REMOTE_HASH=$(git ls-remote origin -h "refs/heads/$BRANCH" | awk '{print $1}' | tr -d '[:space:]')
    LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null | tr -d '[:space:]')
    
    # Check what version is currently running in Docker
    # We use 'tr -d' to ensure no weird whitespace/newlines break the comparison
    RUNNING_HASH=$(docker inspect ttmediabot --format '{{ index .Config.Labels "commit_hash" }}' 2>/dev/null | tr -d '[:space:]')
    [ -z "$RUNNING_HASH" ] && RUNNING_HASH="none"

    # 1. Update Detection Logic
    SHOULD_UPDATE=false
    
    if [ -n "$REMOTE_HASH" ]; then
        if is_behind_remote "$BRANCH" "$LOCAL_HASH" "$REMOTE_HASH"; then
            echo "$(date): New version detected on GitHub ($REMOTE_HASH). Triggering update..."
            SHOULD_UPDATE=true
        elif [ "$LOCAL_HASH" != "$RUNNING_HASH" ]; then
            # We are not behind remote, but the running image doesn't match local code
            # This happens after a manual revert or manual pull.
            echo "$(date): Local code ($LOCAL_HASH) does not match running image ($RUNNING_HASH). Syncing..."
            SHOULD_UPDATE=true
        fi
    fi

    if [ "$SHOULD_UPDATE" = true ]; then
        if [ -f "$LOCK_FILE" ]; then
            echo "$(date): Update already in progress. Skipping cycle..."
        else
            touch "$LOCK_FILE"
            echo "$(date): Running update.sh..."
            # Pass AUTO_UPDATE=true to skip service restarts within the script that would kill this process
            export AUTO_UPDATE=true
            ./update.sh
            unset AUTO_UPDATE
            rm -f "$LOCK_FILE"
        fi
    fi
    sleep 20
done
# Final test commit - Thu Apr 23 06:18:02 UTC 2026
# TTMediaBot Auto-Updater v1.1 - Fully Operational
