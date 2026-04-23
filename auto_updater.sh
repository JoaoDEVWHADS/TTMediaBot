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

while true; do
    # Get current branch name
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "master")
    
    # Check remote hash using ls-remote (bypass rate limits)
    REMOTE_HASH=$(git ls-remote origin -h "refs/heads/$BRANCH" | awk '{print $1}' | tr -d '[:space:]')
    LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null | tr -d '[:space:]')
    
    # Check what version is currently running in Docker
    # We use 'tr -d' to ensure no weird whitespace/newlines break the comparison
    RUNNING_HASH=$(docker inspect ttmediabot --format '{{ index .Config.Labels "commit_hash" }}' 2>/dev/null | tr -d '[:space:]')
    [ -z "$RUNNING_HASH" ] && RUNNING_HASH="none"

    if [ -n "$REMOTE_HASH" ] && { [ "$REMOTE_HASH" != "$LOCAL_HASH" ] || [ "$REMOTE_HASH" != "$RUNNING_HASH" ]; }; then
        if [ -f "$LOCK_FILE" ]; then
            echo "$(date): Update already in progress. Skipping cycle..."
        else
            touch "$LOCK_FILE"
            echo "$(date): Out of sync detected (Remote: $REMOTE_HASH, Local: $LOCAL_HASH, Running: $RUNNING_HASH). Running update.sh..."
            # Pass AUTO_UPDATE=true to skip service restarts within the script that would kill this process
            # Correct variable scope for pipes via export:
            export AUTO_UPDATE=true
            yes | ./update.sh
            unset AUTO_UPDATE
            rm -f "$LOCK_FILE"
        fi
    fi
    sleep 20
done
# Final test commit - Thu Apr 23 06:18:02 UTC 2026
# TTMediaBot Auto-Updater v1.1 - Fully Operational
