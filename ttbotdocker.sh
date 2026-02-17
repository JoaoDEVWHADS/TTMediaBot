#!/bin/bash

# Auto-detect script location and set paths dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOTS_ROOT="${SCRIPT_DIR}/bots"
CONFIG_SOURCE="config.json"

# Configuration
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
    echo -e "${GREEN}      TTMediaBot Docker Manager          ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
}

# Function: Install Dependencies
install_dependencies() {
    header
    echo -e "${YELLOW}Checking dependencies...${NC}"

    if ! command -v docker &> /dev/null; then
        echo "Docker not found. Installing via official repository..."
        
        # 1. Update apt and install prerequisites
        apt-get update
        apt-get install -y ca-certificates curl gnupg lsb-release

        # 2. Add Docker's official GPG key
        mkdir -p /etc/apt/keyrings
        # Remove existing docker.gpg to avoid replacement prompt
        rm -f /etc/apt/keyrings/docker.gpg
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg

        # 3. Set up the repository (using lsb_release to detect distro codename automatically)
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

        # 4. Install Docker Engine
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # 5. Enable service and add user to group
        systemctl enable --now docker
        
        # Add the non-root user who called sudo to the docker group
        REAL_USER=${SUDO_USER:-$USER}
        if [ "$REAL_USER" != "root" ]; then
            usermod -aG docker "$REAL_USER"
            echo "User '$REAL_USER' added to the docker group."
        fi
    else
        echo -e "${GREEN}Docker is already installed.${NC}"
    fi

    if ! command -v jq &> /dev/null; then
        echo "jq not found. Installing..."
        apt-get install -y jq
    else
        echo -e "${GREEN}jq is already installed.${NC}"
    fi
    sleep 2
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
            
            docker run -d \
              --name "$bot_name" \
              --restart unless-stopped \
              -v "$d/config.json":/home/ttbot/TTMediaBot/config.json \
              -v "$d/cookies.txt":/home/ttbot/TTMediaBot/cookies.txt \
              --label "role=ttmediabot" \
              "$BOT_IMAGE" >/dev/null 2>&1
              
            echo -e "  ${GREEN}✓ Container '$bot_name' updated${NC}"
        fi
    done
}

# Function: Build Docker Image
build_image() {
    header
    echo -e "${YELLOW}Checking Docker image '${BOT_IMAGE}'...${NC}"
    
    # Check if Dockerfile exists in current directory
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}Error: Dockerfile not found in current directory!${NC}"
        echo "Please run this script in the folder where the TTMediaBot Dockerfile is located."
        exit 1
    fi

    if [[ "$(docker images -q ${BOT_IMAGE} 2> /dev/null)" == "" ]]; then
        echo "Image not found. Building image..."
        docker build --build-arg CACHEBUST=$(date +%s) -t ${BOT_IMAGE} .
        if [ $? -eq 0 ]; then
             echo -e "${GREEN}Image built successfully!${NC}"
        else
             echo -e "${RED}Error building image! Check the Dockerfile.${NC}"
             exit 1
        fi
        sleep 2
    else
        echo -e "${GREEN}Image '${BOT_IMAGE}' already exists.${NC}"
        # No prompt. User can rebuild via menu option 5.
    fi
}

# Function: Create Bot
create_bot() {
    header
    echo -e "${YELLOW} --- Create New Bot --- ${NC}"
    
    if [ ! -f "$CONFIG_SOURCE" ]; then
       echo -e "${RED}Error: File '$CONFIG_SOURCE' not found in current directory.${NC}"
       return
    fi
    
    read -p "Bot Name (will be the folder name and container name): " bot_name
    if [[ -z "$bot_name" ]]; then echo -e "${RED}Invalid name.${NC}"; sleep 2; return; fi
    
    BOT_DIR="${BOTS_ROOT}/${bot_name}"
    
    # Check if container with this name exists
    if [ "$(docker ps -a -q -f name=^/${bot_name}$)" ]; then
        echo -e "${RED}Error: A container with the name '${bot_name}' already exists.${NC}"
        sleep 2
        return
    fi
    
    if [ -d "$BOT_DIR" ]; then
        echo -e "${RED}A folder for this bot already exists!${NC}"
        sleep 2
        return
    fi

    # Read config template
    # Here assuming we just copy the template and modify with sed or jq, but a simple interactive way is safer.
    # The original script used 'sed' on the copied file.
    
    mkdir -p "$BOT_DIR"
    cp "$CONFIG_SOURCE" "$BOT_DIR/config.json"
    touch "$BOT_DIR/cookies.txt"

    # Minimal Interactive Config
    echo "Configure Bot Settings:"
    read -p "TeamTalk Server Address: " server_addr
    read -p "TCP Port (Default 10333): " tcp_port
    tcp_port=${tcp_port:-10333}
    read -p "UDP Port (Default 10333): " udp_port
    udp_port=${udp_port:-10333}
    
    echo "Encrypted?"
    echo "1. No (False)"
    echo "2. Yes (True)"
    read -p "Option: " encrypted_opt
    if [ "$encrypted_opt" == "2" ]; then encrypted="true"; else encrypted="false"; fi
    
    read -p "Username: " username
    read -sp "Password: " password
    echo ""
    read -p "Bot Nickname (Default: TTMediaBot): " nickname
    nickname=${nickname:-TTMediaBot}
    read -p "Full path to cookies file (Ex: /root/cookies.txt): " cookies_path
    
    
    
    # Batch create option - ask BEFORE creating
    echo ""
    read -p "Batch create? (y/N): " batch_create
    additional_bots=0
    nickname_base=""
    container_base=""
    
    if [[ "$batch_create" =~ ^[yY]$ ]]; then
        read -p "How many additional bots? " additional_bots
        read -p "Base/Prefix for Bot Name (e.g. MyBot -> MyBot1, MyBot2...): " container_base
        read -p "Base/Prefix for Nickname (e.g. DJ -> DJ1, DJ2...): " nickname_base
    fi
    
    # Use jq to update the main config.json
    tmp_config=$(mktemp)
    jq --arg host "$server_addr" \
       --arg tcp "$tcp_port" \
       --arg udp "$udp_port" \
       --argjson enc "$encrypted" \
       --arg user "$username" \
       --arg pass "$password" \
       --arg nick "$nickname" \
       '.teamtalk.host = $host | .teamtalk.tcp_port = ($tcp|tonumber) | .teamtalk.udp_port = ($udp|tonumber) | .teamtalk.encrypted = $enc | .teamtalk.username = $user | .teamtalk.password = $pass | .teamtalk.nickname = $nick' \
       "$BOT_DIR/config.json" > "$tmp_config" && mv "$tmp_config" "$BOT_DIR/config.json"
       
    # Handle Cookies
    if [ -f "$cookies_path" ]; then
        cp "$cookies_path" "$BOT_DIR/cookies.txt"
        echo "Cookies copied."
    fi

    echo "Starting container..."
    docker run -d \
      --name "$bot_name" \
      --restart unless-stopped \
      -v "$BOT_DIR/config.json":/home/ttbot/TTMediaBot/config.json \
      -v "$BOT_DIR/cookies.txt":/home/ttbot/TTMediaBot/cookies.txt \
      --label "role=ttmediabot" \
      "$BOT_IMAGE" >/dev/null 2>&1
      
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Bot '$bot_name' created successfully!${NC}"
    else
        echo -e "${RED}Failed to create bot container.${NC}"
    fi

    # Batch creation loop
    if [[ "$batch_create" =~ ^[yY]$ ]] && [ "$additional_bots" -gt 0 ]; then
        echo "Creating $additional_bots additional bots..."
        for ((i=1; i<=additional_bots; i++)); do
            new_name="${container_base}${i}"
            new_nick="${nickname_base}${i}"
            new_dir="${BOTS_ROOT}/${new_name}"
            
            echo "Creating $new_name ($new_nick)..."
            
             if [ -d "$new_dir" ] || [ "$(docker ps -a -q -f name=^/${new_name}$)" ]; then
                echo -e "${RED}Skipping '$new_name' (exists).${NC}"
                continue
            fi
            
            mkdir -p "$new_dir"
            # Update config with new nickname
            jq --arg nick "$new_nick" '.teamtalk.nickname = $nick' "$BOT_DIR/config.json" > "$new_dir/config.json"
            cp "$BOT_DIR/cookies.txt" "$new_dir/cookies.txt"
            
            docker run -d \
              --name "$new_name" \
              --restart unless-stopped \
              -v "$new_dir/config.json":/home/ttbot/TTMediaBot/config.json \
              -v "$new_dir/cookies.txt":/home/ttbot/TTMediaBot/cookies.txt \
              --label "role=ttmediabot" \
              "$BOT_IMAGE" >/dev/null 2>&1
        done
        echo "Batch creation complete."
    fi
    
    read -p "Press Enter to return..."
    header
}

# Function: Manage Bots
manage_bots() {
    while true; do
        header
        echo -e "${YELLOW} --- Manage Bots --- ${NC}"
        echo "0. Back to Main Menu"
        echo ""
        
        # List running bots
        echo "Running Bots:"
        docker ps --format "table {{.Names}}\t{{.Status}}" -f "label=role=ttmediabot" | sed '1d' | nl -s ". "
        
        # Get bot names into an array
        bots=($(docker ps --format "{{.Names}}" -f "label=role=ttmediabot"))
        count=${#bots[@]}
        
        if [ $count -eq 0 ]; then
            echo "No bots running."
            read -p "Press Enter to return..."
            return
        fi
        
        echo ""
        read -p "Select a bot number to manage (or 0 to back): " selection
        
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -gt 0 ] && [ "$selection" -le "$count" ]; then
            bot_name=${bots[$((selection-1))]}
            manage_single_bot "$bot_name"
        elif [ "$selection" -eq 0 ]; then
            return
        else
            echo "Invalid selection."
        fi
    done
}

# Function: Manage Single Bot
manage_single_bot() {
    local bot_name=$1
    while true; do
        header
        echo -e "${YELLOW} --- Managing: $bot_name --- ${NC}"
        echo "1. View Logs"
        echo "2. Restart"
        echo "3. Stop"
        echo "4. Delete"
        echo "5. Configure (Nano)"
        echo "6. Back"
        echo ""
        read -p "Choose: " action
        
        case $action in
            1)
                docker logs -f "$bot_name"
                ;;
            2)
                docker restart "$bot_name"
                echo "Restarted."
                sleep 1
                ;;
            3)
                docker stop "$bot_name"
                echo "Stopped."
                sleep 1
                ;;
            4)
                read -p "Are you sure you want to delete '$bot_name'? (y/N): " confirm
                if [[ "$confirm" =~ ^[yY]$ ]]; then
                    docker rm -f "$bot_name"
                    rm -rf "$BOTS_ROOT/$bot_name"
                    echo "Deleted."
                    sleep 1
                    return
                fi
                ;;
            5)
                nano "$BOTS_ROOT/$bot_name/config.json"
                echo "Restarting bot to apply changes..."
                docker restart "$bot_name"
                sleep 1
                ;;
            6)
                return
                ;;
            *)
                echo "Invalid option."
                ;;
        esac
    done
}

# Function: Uninstall Everything
uninstall_all() {
    header
    echo -e "${RED}!!! WARNING: THIS WILL DELETE ALL BOTS AND IMAGES !!!${NC}"
    read -p "Are you sure? (type 'yes' to confirm): " confirm
    
    if [ "$confirm" == "yes" ]; then
        echo "Stopping and removing containers..."
        docker ps -a -q -f "label=role=ttmediabot" | xargs -r docker rm -f
        
        echo "Removing image..."
        docker rmi -f "$BOT_IMAGE"
        
        echo "Removing bot files..."
        rm -rf "$BOTS_ROOT"
        
        echo -e "${GREEN}Cleanup complete.${NC}"
        exit 0
    else
        echo "Cancelled."
    fi
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
    
    echo -e "${YELLOW}Building new image...${NC}"
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
    fi
    sleep 2
}

# Function: Force Rebuild Image (Menu Option)
force_rebuild_image() {
    header
    echo -e "${YELLOW} --- Rebuild Docker Image --- ${NC}"
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}Error: Dockerfile not found in current directory!${NC}"
        read -p "Enter to return..."
        return
    fi
    
    echo "This will check for code updates (local files) and rebuild the image."
    echo "Existing bots will be restarted with the new code."
    echo ""
    read -p "Are you sure? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[yY]$ ]]; then
        perform_image_rebuild
    else
        echo "Cancelled."
    fi
    
    read -p "Press Enter to return..."
    header
}

# Function: Update & Fix Permissions
update_and_fix_permissions() {
    header
    echo -e "${YELLOW} --- Update & Fix Permissions --- ${NC}"
    
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
        read -p "Press Enter to continue (will still fix permissions)..."
    else
        # Convert to Unix timestamp
        REMOTE_TS=$(date -d "$LATEST_COMMIT_DATE" +%s)
        
        # Get local file modification date (of this script)
        LOCAL_TS=$(stat -c %Y "$0")
        
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
                    touch "$0"
                    
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
    
    read -p "Press Enter to return..."
    header
}


# Check/Install Deps first
install_dependencies
build_image

# Main Menu
mkdir -p "$BOTS_ROOT"

# Show menu once
while true; do
    header
    echo "1. Create Bot"
    echo "2. Manage Bots"
    echo "3. Uninstall Everything (Total Cleanup)"
    echo "4. Update & Fix Permissions"
    echo "5. Rebuild Docker Image"
    echo "6. Exit"
    echo ""
    read -p "Choose an option: " option
    
    case $option in
        1)
            create_bot
            ;;
        2)
            manage_bots
            ;;
        3)
            uninstall_all
            ;;
        4)
            update_and_fix_permissions
            ;;
        5)
            force_rebuild_image
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option."
            sleep 1
            ;;
    esac
done
