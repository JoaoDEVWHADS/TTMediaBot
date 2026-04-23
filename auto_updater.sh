#!/bin/bash
# TTMediaBot Auto-Updater Watcher
# This script polls GitHub every 20 seconds and runs update.sh if a new commit is detected.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "TTMediaBot Auto-Updater started. Checking every 20 seconds..."

while true; do
    # Get current branch name
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "master")
    
    # Check remote hash using ls-remote (bypass rate limits)
    REMOTE_HASH=$(git ls-remote origin -h "refs/heads/$BRANCH" | awk '{print $1}')
    LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null)

    if [ -n "$REMOTE_HASH" ] && [ "$REMOTE_HASH" != "$LOCAL_HASH" ]; then
        echo "$(date): New update detected ($REMOTE_HASH). Running update.sh..."
        # Use 'yes' to auto-confirm prompts in update.sh
        yes | ./update.sh
    fi
    sleep 20
done
