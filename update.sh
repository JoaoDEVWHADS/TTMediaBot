#!/bin/bash

# Auto-detect script location and set paths dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOTS_ROOT="${SCRIPT_DIR}/bots"
BOT_IMAGE="ttmediabot"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function: Display Header
header() {
    clear
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}      TTMediaBot Update Utility          ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
}

# Function: Recreate Bot Containers
recreate_bot_containers() {
    echo -e "${YELLOW}Recreating containers with the new image...${NC}"
    
    if [ ! -d "$BOTS_ROOT" ]; then return; fi
    
    # Get all bot directories
    for d in "$BOTS_ROOT"/*; do
        if [ -d "$d" ]; then
            bot_name=$(basename "$d")
            
            # Remove existing container if it exists
            if [ "$(docker ps -a -q -f name=^/${bot_name}$)" ]; then
                docker rm -f "$bot_name" >/dev/null 2>&1
            fi
            
            # Recreate
            # Ensure cookies.txt exists just in case
            if [ ! -f "$d/cookies.txt" ]; then touch "$d/cookies.txt"; fi
            
            docker create \
                --name "${bot_name}" \
                --network host \
                --label "role=ttmediabot" \
                --restart always \
                -v "${d}:/home/ttbot/TTMediaBot/data" \
                -v "${d}/cookies.txt:/home/ttbot/TTMediaBot/data/cookies.txt" \
                "${BOT_IMAGE}" > /dev/null 2>&1
                
            if [ $? -eq 0 ]; then
                echo "  ✓ Container '$bot_name' updated"
            else
                echo "  ✗ Error updating '$bot_name'"
            fi
        fi
    done
}

# Function: Perform Image Rebuild (Internal)
perform_image_rebuild() {
    echo ""
    echo -e "${YELLOW}Starting Image Rebuild...${NC}"
    
    # Capture NAMES of running bots to restart them later
    # We also check a persistent state file in case a previous update was interrupted after stopping bots
    STATE_FILE="/tmp/ttmediabot_last_running.txt"
    RUNNING_NAMES=$(docker ps --format "{{.Names}}" -f "label=role=ttmediabot")
    
    if [ -z "$RUNNING_NAMES" ] && [ -f "$STATE_FILE" ]; then
        RUNNING_NAMES=$(cat "$STATE_FILE")
        echo -e "${YELLOW}Recovery: Found interrupted update state. Will attempt to restart: $RUNNING_NAMES${NC}"
    fi

    if [ ! -z "$RUNNING_NAMES" ]; then
        echo "$RUNNING_NAMES" > "$STATE_FILE"
        echo -e "${YELLOW}Stopping bots for update (User Choice: Stop before Build)...${NC}"
        echo "$RUNNING_NAMES" | xargs docker stop -t 1 > /dev/null 2>&1
    fi

    # Build the image with a commit hash label for version tracking
    CURRENT_HASH=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    echo "Building new image with version label: $CURRENT_HASH"
    docker build --build-arg CACHEBUST=$(date +%s) --label "commit_hash=$CURRENT_HASH" -t ${BOT_IMAGE} .
    
    if [ $? -eq 0 ]; then
         echo -e "${GREEN}Image built successfully!${NC}"
         
         # Recreate containers to use new image
         recreate_bot_containers
         
         if [ ! -z "$RUNNING_NAMES" ]; then
             echo -e "${YELLOW}Restarting active bots...${NC}"
             echo "$RUNNING_NAMES" | xargs docker start > /dev/null 2>&1
             
             # Health Check: Wait for all bots to be confirmed 'running'
             # We wait up to 5 minutes (150 retries * 2s) to accommodate large fleets,
             # but we keep a safety limit to avoid locking the system forever if a bot is broken.
             echo -en "${YELLOW}Verifying bot health (Timeout: 5m)...${NC} "
             MAX_RETRIES=150
             RETRY_COUNT=0
             while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                 TOTAL_BOTS=$(echo "$RUNNING_NAMES" | wc -w)
                 # Check for both 'running' and 'restarting' (since a bot might be in a fast crash loop but it means it "tried" to start)
                 STABLE_BOTS=$(docker ps -a --filter "status=running" --filter "status=restarting" --format "{{.Names}}" | grep -xF "$RUNNING_NAMES" | wc -l)
                 
                 if [ "$STABLE_BOTS" -ge "$TOTAL_BOTS" ]; then
                     echo -e "[ ${GREEN}OK${NC} ] All $TOTAL_BOTS bots are confirmed active."
                     break
                 fi
                 
                 echo -n "."
                 sleep 2
                 RETRY_COUNT=$((RETRY_COUNT + 1))
             done
             
             if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
                 echo -e "\n${RED}Warning: Some bots might have failed to start or crashed.${NC}"
             else
                 # Success! Clear the persistent state file
                 rm -f "$STATE_FILE"
             fi
         fi
    else
         echo -e "${RED}Error building image!${NC}"
         exit 1
    fi
    sleep 2
}

# Function: Update & Fix Permissions
update_and_fix_permissions() {
    # Lock protection to avoid race conditions (Commit A vs Commit B)
    # If AUTO_UPDATE=true, the lock is handled by the parent service (auto_updater.sh)
    # If called manually, we check and create it to avoid overlapping with the auto-updater.
    LOCK_FILE="/tmp/ttmediabot_update.lock"
    if [ "$AUTO_UPDATE" != "true" ]; then
        if [ -f "$LOCK_FILE" ]; then
            echo -e "${RED}Error: Another update is already in progress.${NC}"
            echo "Waiting for it to finish..."
            while [ -f "$LOCK_FILE" ]; do sleep 2; done
            echo "Lock released. Proceeding..."
        fi
        touch "$LOCK_FILE"
        trap 'rm -f "$LOCK_FILE"' EXIT INT TERM
    fi

    header
    echo -e "${YELLOW} --- Update & Auto-Fix --- ${NC}"
    
    # 1. Determine REAL user
    REAL_USER=${SUDO_USER:-$USER}
    
    if [ "$REAL_USER" == "root" ]; then
         # Fallback 1: Check owner of the script directory
         SCRIPT_OWNER=$(stat -c '%U' "$SCRIPT_DIR")
         if [ "$SCRIPT_OWNER" != "root" ]; then
             REAL_USER="$SCRIPT_OWNER"
         else
             # Fallback 2: Check owner of parent directory
             PARENT_DIR=$(dirname "$SCRIPT_DIR")
             PARENT_OWNER=$(stat -c '%U' "$PARENT_DIR")
             if [ "$PARENT_OWNER" != "root" ]; then
                 REAL_USER="$PARENT_OWNER"
             else
                 # Fallback 3: Use root automatically
                 echo -e "${YELLOW}Could not detect non-root user. Using 'root' automatically.${NC}"
                 REAL_USER="root"
             fi
         fi
    fi

    echo -e "${YELLOW}Target User: ${REAL_USER}${NC}"
    echo ""

    # 2. Check for Updates (GitHub API vs Local Date)
    REPO_OWNER="JoaoDEVWHADS"
    REPO_NAME="TTMediaBot"
    BRANCH="master"
    
    echo -e "${YELLOW}Checking for updates...${NC}"
    
    # Check if we are in a git repository
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        # Fetch remote info
        git fetch origin "$BRANCH" -q
        REMOTE_HASH=$(git rev-parse "origin/$BRANCH" | tr -d '[:space:]')
        LOCAL_HASH=$(git rev-parse HEAD | tr -d '[:space:]')
        
        # Check running version
        # Use 'tr -d' to ensure no weird whitespace/newlines break the comparison
        RUNNING_HASH=$(docker inspect ${BOT_IMAGE} --format '{{ index .Config.Labels "commit_hash" }}' 2>/dev/null | tr -d '[:space:]')
        [ -z "$RUNNING_HASH" ] && RUNNING_HASH="none"
        
        # Determine if we need an update or a rebuild
        NEEDS_PULL=false
        NEEDS_REBUILD=false
        
        # Check for uncommitted local changes
        LOCAL_CHANGES=$(git status --porcelain)
        HAS_LOCAL_CHANGES=false
        if [ -n "$LOCAL_CHANGES" ]; then
            HAS_LOCAL_CHANGES=true
        fi
        
        # Check if local is behind remote
        if [ "$REMOTE_HASH" != "$LOCAL_HASH" ]; then
            if git merge-base --is-ancestor "$LOCAL_HASH" "$REMOTE_HASH"; then
                NEEDS_PULL=true
                echo -e "${YELLOW}Local version is behind remote.${NC}"
            else
                echo -e "${YELLOW}Local version has diverged or is ahead of remote. Auto-pull skipped to protect local changes.${NC}"
                NEEDS_PULL=false
            fi
        fi

        if [ "$HAS_LOCAL_CHANGES" = true ]; then
             echo -e "${RED}Warning: You have uncommitted local changes!${NC}"
             NEEDS_PULL=false # Default to false for safety if we have local changes
        fi
        
        if [ "$LOCAL_HASH" != "$RUNNING_HASH" ]; then
            NEEDS_REBUILD=true
        fi
        
        if [ "$NEEDS_PULL" = true ] || [ "$NEEDS_REBUILD" = true ]; then
            # Improved detection: Check for existance of image or bots directory/config
            IMAGE_EXISTS=$(docker images -q ${BOT_IMAGE} 2>/dev/null)
            
            if [ -z "$IMAGE_EXISTS" ] && [ ! -d "$BOTS_ROOT" ] && [ ! -f "$SCRIPT_DIR/config.json" ]; then
                echo -e "${GREEN}Initial Setup / Installation Required!${NC}"
                IS_FIRST_INSTALL=true
            else
                echo -e "${GREEN}Update or Version mismatch found!${NC}"
                IS_FIRST_INSTALL=false
                if [ "$RUNNING_HASH" == "none" ]; then
                    echo -e "${YELLOW}Note: Running image exists but is missing version label.${NC}"
                fi
            fi
            echo "Remote:  $REMOTE_HASH"
            echo "Local:   $LOCAL_HASH"
            echo "Running: $RUNNING_HASH"
            UPDATE_FOUND=true
            # If we need a rebuild, ensure UPDATE_PERFORMED will be true later
            [ "$NEEDS_REBUILD" = true ] && REBUILD_REQUIRED=true
        else
            echo -e "${GREEN}Already up to date and running latest version ($LOCAL_HASH).${NC}"
            UPDATE_FOUND=false
        fi
    else
        # Fallback to date-based check if not a git repo yet (first install)
        LATEST_COMMIT_DATE=$(curl -s "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/commits/$BRANCH" | jq -r '.commit.committer.date')
        
        if [ -n "$LATEST_COMMIT_DATE" ] && [ "$LATEST_COMMIT_DATE" != "null" ]; then
            REMOTE_TS=$(date -d "$LATEST_COMMIT_DATE" +%s)
            LOCAL_TS=$(stat -c %Y "$SCRIPT_DIR/ttbotdocker.sh" 2>/dev/null || echo 0)
            
            if [ "$REMOTE_TS" -gt "$LOCAL_TS" ]; then
                echo -e "${GREEN}Update found (date-based)!${NC}"
                UPDATE_FOUND=true
            else
                echo -e "${GREEN}Already up to date (date-based).${NC}"
                UPDATE_FOUND=false
            fi
        else
            # If API fails, assume we might need update if we aren't a git repo
            echo -e "${RED}Warning: Could not check updates via API (rate limit?).${NC}"
            UPDATE_FOUND=false
        fi
    fi

    UPDATE_PERFORMED=false
    
    if [ "$UPDATE_FOUND" == "true" ]; then
        echo ""
        if [ "$IS_FIRST_INSTALL" == "true" ]; then
            echo "This will:"
            echo "1. Clone/pull the latest repository code"
            echo "2. Build and setup the TTMediaBot Docker image"
            echo "3. Initialize environment and fix permissions"
        else
            echo "This will:"
            echo "1. Backup 'bots' folder (configs/cookies)"
            echo "2. Clone/pull the latest repository code"
            echo "3. Update all local files"
            echo "4. Restore backup"
        fi
        echo ""
        
        if [ "$AUTO_UPDATE" = "true" ]; then
            echo "Auto-Update mode detected. Proceeding automatically..."
            confirm_update="y"
            # In auto-update, if we have local changes, we should probably skip to avoid data loss
            if [ "$HAS_LOCAL_CHANGES" = true ]; then
                echo -e "${RED}Auto-update skipped because of local changes.${NC}"
                confirm_update="n"
            fi
        else
            echo -e "${YELLOW}Local changes detected: ${HAS_LOCAL_CHANGES}${NC}"
            if [ "$HAS_LOCAL_CHANGES" = true ]; then
                echo -e "${RED}WARNING: Proceeding will OVERWRITE your local uncommitted changes!${NC}"
                read -p "Do you REALLY want to overwrite your changes and update? [y/N]: " confirm_update
            else
                read -p "Update found. Do you want to proceed? [y/N]: " confirm_update
            fi
        fi
            
        if [[ "$confirm_update" =~ ^[yY]$ ]]; then
                echo -e "${YELLOW}Starting update...${NC}"
                
                # Check if we are in a git repository
                if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
                    echo "Performing forced synchronization with GitHub..."
                    # Backup configs before sync just in case
                    TMP_BACKUP=$(mktemp -d)
                    if [ -d "$BOTS_ROOT" ]; then 
                        mkdir -p "$TMP_BACKUP/bots"
                        cp -r "$BOTS_ROOT/." "$TMP_BACKUP/bots/"
                    fi
                    
                    # Force synchronization to match origin exactly
                    git fetch origin "$BRANCH"
                    git reset --hard "origin/$BRANCH"
                    git clean -fd # Also remove untracked files that might conflict
                    
                    # Restore backup if needed
                    if [ -d "$TMP_BACKUP/bots" ]; then 
                        cp -rf "$TMP_BACKUP/bots/." "$BOTS_ROOT/" 2>/dev/null
                    fi
                    rm -rf "$TMP_BACKUP"
                    
                    UPDATE_PERFORMED=true
                else
                    # First time conversion to git repo or standalone install
                    # Define Temp Dirs
                    TMP_DIR=$(mktemp -d)
                    BACKUP_DIR="$TMP_DIR/backup"
                    mkdir -p "$BACKUP_DIR"
                    
                    # 1. Backup Configs
                    echo "Backing up configurations..."
                    if [ -d "$BOTS_ROOT" ]; then cp -r "$BOTS_ROOT" "$BACKUP_DIR/"; fi
                    
                    # 2. Clone Repository
                    echo "Cloning repository..."
                    CLONE_DIR="$TMP_DIR/clone"
                    git clone "https://github.com/$REPO_OWNER/$REPO_NAME.git" "$CLONE_DIR"
                    
                    if [ $? -eq 0 ]; then
                        echo "Installing..."
                        cp -rf "$CLONE_DIR/." "$SCRIPT_DIR/"
                        
                        # 4. Restore Backup
                        if [ -d "$BACKUP_DIR/bots" ]; then cp -rf "$BACKUP_DIR/bots/"* "$BOTS_ROOT/" 2>/dev/null; fi
                        
                        UPDATE_PERFORMED=true
                        rm -rf "$TMP_DIR"
                    else
                        echo -e "${RED}Clone failed.${NC}"
                    fi
                fi

                if [ "$UPDATE_PERFORMED" == "true" ]; then
                     # Update timestamp
                     touch "$SCRIPT_DIR/ttbotdocker.sh"
                     echo -e "${GREEN}Update applied!${NC}"
                fi
            else
                echo "Update cancelled."
                exit 0
            fi
        fi
    
    if [ "$UPDATE_PERFORMED" == "true" ] || [ "$REBUILD_REQUIRED" == "true" ]; then
        echo ""
        echo -e "${YELLOW}Fixing permissions...${NC}"
        
        # 4. Fix permissions
        # Operate on SCRIPT_DIR
        TARGET_FIX_DIR="$SCRIPT_DIR"
        TARGET_FIX_DIR=$(realpath "$TARGET_FIX_DIR")
        
        echo "Setting ownership to $REAL_USER:$REAL_USER for $TARGET_FIX_DIR..."
        chown -R "$REAL_USER":"$REAL_USER" "$TARGET_FIX_DIR"
        
        echo "Setting permissions (777 - Full Control)..."
        chmod -R 777 "$TARGET_FIX_DIR"
        
        chmod +x "$TARGET_FIX_DIR"/*.sh 2>/dev/null
        
        echo ""
        echo -e "${GREEN}Done! Permissions set to User: $REAL_USER, Mode: 777.${NC}"
    fi
    
    # 5. Auto-Rebuild (if update occurred or version mismatch detected)
    if [ "$UPDATE_PERFORMED" == "true" ] || [ "$REBUILD_REQUIRED" == "true" ]; then
        echo ""
        echo -e "${YELLOW}Update applied or version mismatch detected. Rebuilding Docker image...${NC}"
        # Wait a bit
        sleep 2
        perform_image_rebuild
    fi
    
    # Return to script dir
    cd "$SCRIPT_DIR" || return
}

# Function: Configure Auto-Updater Service
configure_auto_updater() {
    # Check if masked - respect user choice to disable
    if LANG=C systemctl list-unit-files ttmediabot-updater.service 2>/dev/null | grep -q "masked"; then
        echo -e "${YELLOW}Auto-Updater is currently masked. Skipping configuration to respect manual override.${NC}"
        return
    fi

    echo ""
    echo -e "${YELLOW} --- Configuring Auto-Updater Service --- ${NC}"
    
    SERVICE_FILE="/etc/systemd/system/ttmediabot-updater.service"
    
    # Create the service file
    echo "Creating systemd service..."
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=TTMediaBot Auto-Updater Watcher
After=network.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=/bin/bash $SCRIPT_DIR/auto_updater.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

    # Fix permissions for the watcher script
    chmod +x "$SCRIPT_DIR/auto_updater.sh"

    # Reload systemd and enable service
    echo "Enabling and starting service..."
    systemctl daemon-reload
    systemctl enable ttmediabot-updater.service >/dev/null 2>&1
    
    # Only restart if not being called by the auto-updater to avoid killing our own process
    if [ "$AUTO_UPDATE" != "true" ]; then
        systemctl restart --no-block ttmediabot-updater.service
        echo -e "${GREEN}Auto-Updater Service configured and restarting in background!${NC}"
    else
        echo -e "${GREEN}Auto-Updater Service configured (restart skipped to avoid interruption).${NC}"
    fi
}
# Run
install_deps_light() {
    if ! command -v jq &> /dev/null; then apt-get install -y jq; fi
    if ! command -v git &> /dev/null; then apt-get install -y git; fi
    if ! command -v curl &> /dev/null; then apt-get install -y curl; fi
}

# --- MAIN EXECUTION WRAPPER ---
# Wrapping in a main function ensures bash loads the entire block into memory
# protecting against crashes if the script modifies itself mid-execution during git reset.
main() {
    install_deps_light
    update_and_fix_permissions
    
    # The user mandated that service configuration MUST run every time
    # but not block the flow (implemented via --no-block inside the function).
    configure_auto_updater
}

# Execute main in memory
main "$@"
exit 0
