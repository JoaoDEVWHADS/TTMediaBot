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
    echo "Checking running bots..."
    
    # Capture NAMES of running bots to restart them later
    RUNNING_NAMES=$(docker ps --format "{{.Names}}" -f "label=role=ttmediabot")
    
    if [ ! -z "$RUNNING_NAMES" ]; then
        echo -e "${YELLOW}Stopping bots for update...${NC}"
        echo "$RUNNING_NAMES" | xargs docker stop -t 1 > /dev/null 2>&1
    fi
    
    echo -e "${YELLOW}Building new image (updating code, keeping dependencies in cache)...${NC}"
    docker build --build-arg CACHEBUST=$(date +%s) -t ${BOT_IMAGE} .
    
    if [ $? -eq 0 ]; then
         echo -e "${GREEN}Image updated successfully!${NC}"
         
         # Recreate containers to use new image
         recreate_bot_containers
         
         if [ ! -z "$RUNNING_NAMES" ]; then
             echo -e "${YELLOW}Restarting active bots...${NC}"
             echo "$RUNNING_NAMES" | xargs docker start > /dev/null 2>&1
             echo -e "${GREEN}Bots restarted with the new code.${NC}"
         fi
    else
         echo -e "${RED}Error building image!${NC}"
         exit 1
    fi
    sleep 2
}

# Function: Update & Fix Permissions
update_and_fix_permissions() {
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
                 # Fallback 3: Ask user
                 echo -e "${RED}Could not detect non-root user automatically.${NC}"
                 read -p "Enter your system username (for permission fix): " manual_user
                 if [ -n "$manual_user" ]; then
                     REAL_USER="$manual_user"
                 else
                     echo "No user entered. Using 'root'."
                     REAL_USER="root"
                 fi
             fi
         fi
    fi

    echo -e "${YELLOW}Target User: ${REAL_USER}${NC}"
    echo ""

    # 2. Check for Updates (GitHub API vs Local Date)
    REPO_OWNER="JoaoDEVWHADS"
    REPO_NAME="TTMediaBot"
    BRANCH="master"
    
    echo -e "${YELLOW}Checking GitHub for updates...${NC}"
    
    # Get latest commit date from GitHub API
    # returns ISO 8601 date, e.g., "2023-10-27T10:00:00Z"
    LATEST_COMMIT_DATE=$(curl -s "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/commits/$BRANCH" | jq -r '.commit.committer.date')
    
    UPDATE_PERFORMED=false
    
    if [ -z "$LATEST_COMMIT_DATE" ] || [ "$LATEST_COMMIT_DATE" == "null" ]; then
        echo -e "${RED}Error fetching update info from GitHub.${NC}"
        echo "Check internet connection or API rate limits."
        exit 1
    else
        # Convert to Unix timestamp
        REMOTE_TS=$(date -d "$LATEST_COMMIT_DATE" +%s)
        
        # Get local file modification date (of this script)
        LOCAL_TS=$(stat -c %Y "$SCRIPT_DIR/ttbotdocker.sh")
        
        # Compare
        if [ "$REMOTE_TS" -gt "$LOCAL_TS" ]; then
            echo -e "${GREEN}Update found!${NC}"
            echo "Remote: $(date -d @$REMOTE_TS)"
            echo "Local:  $(date -d @$LOCAL_TS)"
            echo ""
            echo "This will:"
            echo "1. Backup 'bots' folder (configs/cookies)"
            echo "2. Clone the latest repository code"
            echo "3. Replace all local files with the cloned version"
            echo "4. Restore backup"
            echo "5. Convert installation to a valid Git repository"
            echo ""
            read -p "Proceed? (y/N): " confirm_update
            
            if [[ "$confirm_update" =~ ^[yY]$ ]]; then
                echo -e "${YELLOW}Starting update...${NC}"
                
                # Define Temp Dirs
                TMP_DIR=$(mktemp -d)
                BACKUP_DIR="$TMP_DIR/backup"
                mkdir -p "$BACKUP_DIR"
                
                # 1. Backup Configs
                echo "Backing up configurations..."
                
                if [ -d "$BOTS_ROOT" ]; then
                    cp -r "$BOTS_ROOT" "$BACKUP_DIR/"
                fi
                
                # 2. Clone Repository (Full Git Init)
                echo "Cloning repository..."
                CLONE_DIR="$TMP_DIR/clone"
                
                # Clone to temp dir
                git clone "https://github.com/$REPO_OWNER/$REPO_NAME.git" "$CLONE_DIR"
                
                if [ $? -ne 0 ]; then
                    echo -e "${RED}Clone failed.${NC}"
                else
                    echo "Installing..."
                    
                    # Debug info
                    echo "Cloned content:"
                    ls -A "$CLONE_DIR" | head -n 5
                    echo "..."
                    
                    # Copy files over, overwriting
                    # Use /. to include hidden files (especially .git)
                    # This converts the local folder into a git repo if it wasn't one
                    cp -rf "$CLONE_DIR/." "$SCRIPT_DIR/"
                    
                    # 4. Restore Backup
                    echo "Restoring configurations..."
                    if [ -d "$BACKUP_DIR/bots" ]; then
                        # Restore bots folder
                        cp -rf "$BACKUP_DIR/bots/"* "$BOTS_ROOT/" 2>/dev/null
                    fi
                    
                    # Update timestamp
                    touch "$SCRIPT_DIR/ttbotdocker.sh"
                    
                    echo -e "${GREEN}Update applied! Repository is now git-linked.${NC}"
                    UPDATE_PERFORMED=true
                    
                    # Cleanup
                    echo "Cleaning up..."
                    rm -rf "$TMP_DIR"
                fi
            else
                echo "Update cancelled."
            fi
        else
            echo -e "${GREEN}Already up to date.${NC}"
            echo "Remote: $(date -d @$REMOTE_TS)"
            echo "Local:  $(date -d @$LOCAL_TS)"
        fi
    fi
    
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
    
    # 5. Auto-Rebuild (if update occurred)
    if [ "$UPDATE_PERFORMED" == "true" ]; then
        echo ""
        echo -e "${YELLOW}Since an update was applied, we need to rebuild the Docker image.${NC}"
        # Wait a bit
        sleep 2
        perform_image_rebuild
    fi
    
    # Return to script dir
    cd "$SCRIPT_DIR" || return
}


# Run
install_deps_light() {
    if ! command -v jq &> /dev/null; then apt-get install -y jq; fi
    if ! command -v git &> /dev/null; then apt-get install -y git; fi
    if ! command -v curl &> /dev/null; then apt-get install -y curl; fi
}

install_deps_light
update_and_fix_permissions
