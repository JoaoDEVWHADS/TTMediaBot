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
        # No prompt here anymore
        sleep 1
    fi
}

# Function: Force Rebuild Image (Menu Option)
force_rebuild_image() {
    header
    echo -e "${YELLOW} --- Rebuild Image / Update Code --- ${NC}"
    echo "This will pull the latest changes (if you updated files) and rebuild the Docker image."
    echo ""
    read -p "Are you sure? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
        return
    fi

    echo ""
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
         # Don't exit script, just return to menu
         read -p "Press Enter to continue..."
         return
    fi
    
    read -p "Process completed. Press Enter to return..."
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

    # ... inputs ...
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
    
    read -p "Channel (Default: /): " channel
    channel=${channel:-/}
    read -sp "Channel Password (Default: empty): " channel_password
    echo ""
    
    
    
    # Batch create option - ask BEFORE creating
    echo ""
    read -p "Batch create? (y/N): " batch_create
    additional_bots=0
    nickname_base=""
    container_base=""
    
    if [[ "$batch_create" =~ ^[yY]$ ]]; then
        read -p "How many ADDITIONAL bots to create (besides the main one)?: " additional_bots
        if [[ ! "$additional_bots" =~ ^[0-9]+$ ]] || [ "$additional_bots" -lt 0 ]; then
            echo -e "${RED}Invalid quantity. Creating only the main bot.${NC}"
            additional_bots=0
        fi
        
        if [ "$additional_bots" -gt 0 ]; then
            echo -e "${YELLOW}WARNING: Use a different BASE name for containers to avoid conflicts!${NC}"
            read -p "BASE name for CONTAINERS (Enter = default 'bot'): " container_base
            if [[ -z "$container_base" ]]; then
                container_base="bot"
            fi
            read -p "BASE name for NICKNAMES (Enter = same as container '$container_base'): " nickname_base
            if [[ -z "$nickname_base" ]]; then
                nickname_base="$container_base"
            fi
        else
            # No additional bots, use bot_name as container_base
            container_base="$bot_name"
        fi
    else
        # Single bot creation - use bot_name as container_base
        container_base="$bot_name"
    fi
    
    total_bots=$((additional_bots + 1))
    echo -e "${YELLOW}Creating $total_bots bot(s)...${NC}"
    
    
    # Find highest existing number for both container names and nicknames
    highest_num=0
    base_name_exists=false
    highest_nickname_num=0
    nickname_base_exists=false
    
    if [ -d "$BOTS_ROOT" ] && [ -n "$container_base" ]; then
        for d in "$BOTS_ROOT"/*; do
            if [ -d "$d" ]; then
                name=$(basename "$d")
                
                # Check container names strictly against container_base
                if [[ "$name" == "$container_base" ]]; then
                    base_name_exists=true
                elif [[ "$name" =~ ^${container_base}([0-9]+)$ ]]; then
                    num="${BASH_REMATCH[1]}"
                    [ "$num" -gt "$highest_num" ] && highest_num=$num
                fi
                
                # Check nicknames in config.json strictly against nickname_base
                # BUT ONLY for bots on the SAME SERVER (hostname + port)
                config_file="$d/config.json"
                if [ -f "$config_file" ] && [ -n "$nickname_base" ]; then
                    # Get server info from this bot's config
                    existing_hostname=$(jq -r '.teamtalk.hostname // ""' "$config_file")
                    existing_tcp_port=$(jq -r '.teamtalk.tcp_port // 0' "$config_file")
                    
                    # Only check nicknames if it's the SAME server
                    if [[ "$existing_hostname" == "$server_addr" ]] && [[ "$existing_tcp_port" == "$tcp_port" ]]; then
                        existing_nickname=$(jq -r '.teamtalk.nickname // ""' "$config_file")
                        
                        if [[ "$existing_nickname" == "$nickname_base" ]]; then
                            nickname_base_exists=true
                        elif [[ "$existing_nickname" =~ ^${nickname_base}([0-9]+)$ ]]; then
                            nick_num="${BASH_REMATCH[1]}"
                            [ "$nick_num" -gt "$highest_nickname_num" ] && highest_nickname_num=$nick_num
                        fi
                    fi
                fi
            fi
        done
    fi
    
    # Simple sequential counter for naming
    # When base doesn't exist, we start numbering from 1 (bot, bot1, bot2...)
    # When base exists, we continue from highest_num + 1
    if [ "$base_name_exists" == "true" ]; then
        next_container_num=$((highest_num + 1))
    else
        next_container_num=1
    fi
    
    if [ "$nickname_base_exists" == "true" ]; then
        next_nickname_num=$((highest_nickname_num + 1))
    else
        next_nickname_num=1
    fi
    
    # Track if we've used the base name yet
    container_base_used=$base_name_exists
    nickname_base_used=$nickname_base_exists
    
    # Loop to create bots
    for i in $(seq 1 $total_bots); do
        # Determine container name
        if [ $i -eq 1 ]; then
            # First bot uses container_base
            if [ "$container_base_used" == "false" ]; then
                current_bot_name="$container_base"
                container_base_used=true
            else
                current_bot_name="${container_base}${next_container_num}"
                next_container_num=$((next_container_num + 1))
            fi
            current_nickname="$nickname"
        else
            # Additional bots use container_base for container naming
            # Sequence: bot, bot1, bot2, bot3...
            if [ "$container_base_used" == "false" ]; then
                # Base name not used yet, use it now
                current_bot_name="$container_base"
                container_base_used=true
            else
                # Base name already used, use numbered version
                current_bot_name="${container_base}${next_container_num}"
                next_container_num=$((next_container_num + 1))
            fi
            
            # Nickname follows same logic
            if [ -n "$nickname_base" ]; then
                if [ "$nickname_base_used" == "false" ]; then
                    current_nickname="$nickname_base"
                    nickname_base_used=true
                else
                    current_nickname="${nickname_base}${next_nickname_num}"
                    next_nickname_num=$((next_nickname_num + 1))
                fi
            else
                current_nickname="$current_bot_name"
            fi
        fi
        
        CURRENT_BOT_DIR="${BOTS_ROOT}/${current_bot_name}"
        
        # Check if container exists
        if [ "$(docker ps -a -q -f name=^/${current_bot_name}$)" ]; then
            echo -e "${RED}Skipping '$current_bot_name' (container already exists)${NC}"
            continue
        fi
        
        if [ -d "$CURRENT_BOT_DIR" ]; then
            echo -e "${RED}Skipping '$current_bot_name' (folder already exists)${NC}"
            continue
        fi
        
        echo ""
        echo -e "${YELLOW}Creating bot '$current_bot_name'...${NC}"
        mkdir -p "$CURRENT_BOT_DIR"
    
    # Copy default config
    cp "$CONFIG_SOURCE" "$CURRENT_BOT_DIR/config.json"
    
    # Configure cookies mount
    COOKIES_MOUNT=""
    CONTAINER_COOKIE_PATH=""
    
    if [ -f "$cookies_path" ]; then
        echo "Copying cookies file..."
        cp "$cookies_path" "$CURRENT_BOT_DIR/cookies.txt"
        COOKIES_MOUNT="-v ${CURRENT_BOT_DIR}/cookies.txt:/home/ttbot/TTMediaBot/data/cookies.txt"
        CONTAINER_COOKIE_PATH="data/cookies.txt"
    else
        echo -e "${RED}Cookies file not found! The bot will be created without specific cookies.${NC}"
        # Create empty cookies file to avoid mount errors if referenced
        touch "$CURRENT_BOT_DIR/cookies.txt"
        COOKIES_MOUNT="-v ${CURRENT_BOT_DIR}/cookies.txt:/home/ttbot/TTMediaBot/data/cookies.txt"
        CONTAINER_COOKIE_PATH="data/cookies.txt"
    fi
    
    # Update JSON with jq
    tmp_config=$(mktemp)
    jq --arg host "$server_addr" \
       --argjson tcp "$tcp_port" \
       --argjson udp "$udp_port" \
       --argjson enc "$encrypted" \
       --arg nick "$current_nickname" \
       --arg user "$username" \
       --arg pass "$password" \
       --arg chan "$channel" \
       --arg chan_pass "$channel_password" \
       --arg cookie "$CONTAINER_COOKIE_PATH" \
       '.teamtalk.hostname = $host | 
        .teamtalk.tcp_port = $tcp | 
        .teamtalk.udp_port = $udp | 
        .teamtalk.encrypted = $enc | 
        .teamtalk.nickname = $nick | 
        .teamtalk.username = $user | 
        .teamtalk.password = $pass | 
        .teamtalk.channel = $chan | 
        .teamtalk.channel_password = $chan_pass |
        if $cookie != "" then .services.yt.cookiefile_path = $cookie else . end' \
       "$CURRENT_BOT_DIR/config.json" > "$tmp_config" && mv "$tmp_config" "$CURRENT_BOT_DIR/config.json"

    # Fix permissions for container user (uid 1000 is standard for non-root in many images)
    echo "Adjusting folder permissions..."
    chown -R 1000:1000 "$CURRENT_BOT_DIR"

    echo -e "${YELLOW}Creating container...${NC}"
    # Use label to identify bots later since name is variable
    docker create \
        --name "${current_bot_name}" \
        --network host \
        --label "role=ttmediabot" \
        --restart always \
        -v "${CURRENT_BOT_DIR}:/home/ttbot/TTMediaBot/data" \
        $COOKIES_MOUNT \
        "${BOT_IMAGE}" > /dev/null 2>&1


    if [ $? -eq 0 ]; then
        echo "  ✓ Bot '$current_bot_name' created successfully!"
    else
        echo "  ✗ Error creating '$current_bot_name'"
    fi
    done
    
    echo ""
    echo -e "${YELLOW}Starting all bots in parallel...${NC}"
    # Start all newly created bots in parallel
    docker start $(docker ps -a -q -f "label=role=ttmediabot" -f "status=created") 2>/dev/null
    
    echo -e "${GREEN}Creation completed! $total_bots bot(s) created and started.${NC}"
    read -p "Press Enter to return..."
}

# Function: List Bots
list_bots() {
    echo -e "${YELLOW}Existing Bots:${NC}"
    if [ -d "$BOTS_ROOT" ]; then
        ls -1 "$BOTS_ROOT"
    else
        echo "No bots found."
    fi
        echo ""
}

# Function: Delete Bot
delete_bot() {
    # Show menu once
    header
    while true; do
        echo -e "${YELLOW} --- Delete Bot --- ${NC}"
        
        # Array to store bot names
        bots=()
        if [ -d "$BOTS_ROOT" ]; then
            for d in "$BOTS_ROOT"/*; do
                if [ -d "$d" ]; then
                    bots+=("$(basename "$d")")
                fi
            done
        fi
        
        if [ ${#bots[@]} -eq 0 ]; then
            echo "No bots found."
            read -p "Enter to return..."
            return
        fi
        
        echo "Bots available for deletion:"
        for i in "${!bots[@]}"; do
            # Display 1-based index
            echo "$((i+1)). ${bots[$i]}"
        done
        echo "0. Return"
        echo ""
        
        read -p "Enter the NUMBER of the bot to DELETE: " bot_num
        
        # Handle Empty (Enter key) - Just refresh
        if [[ -z "$bot_num" ]]; then
            echo ""
            continue
        fi
        
        # Handle Return
        if [[ "$bot_num" == "0" ]]; then return; fi
        
        # Validate input
        if [[ ! "$bot_num" =~ ^[0-9]+$ ]] || [ "$bot_num" -lt 1 ] || [ "$bot_num" -gt "${#bots[@]}" ]; then
            # Invalid option - just reprint menu
            echo ""
            continue
        fi
        
        # Get bot name by index (adjust for 1-based input)
        idx=$((bot_num-1))
        bot_to_delete="${bots[$idx]}"
        
        CONTAINER_NAME="${bot_to_delete}"
        BOT_DIR="${BOTS_ROOT}/${bot_to_delete}"
        
        echo -e "${RED}WARNING: This will delete everything about '$bot_to_delete' (Container and Folder).${NC}"
        read -p "Are you sure? (y/N): " confirm
        if [[ "$confirm" =~ ^[yY]$ ]]; then
            echo "1. Removing Container..."
            docker stop -t 1 "$CONTAINER_NAME" >/dev/null 2>&1
            docker rm "$CONTAINER_NAME" >/dev/null 2>&1
            echo "   OK (If existed)."
            
            echo "2. Removing Folder..."
            if [ -d "$BOT_DIR" ]; then
                rm -rf "$BOT_DIR"
                echo "   Folder removed: $BOT_DIR"
            else
                echo "   Folder not found (already removed)."
            fi
            
            echo -e "${GREEN}Cleanup completed for '$bot_to_delete'.${NC}"
            read -p "Press Enter to continue..."
            # Refresh menu after deletion
            header
        else
            echo "Cancelled."
            echo ""
        fi
    done
}

# Function: Delete Multiple Bots at Once
delete_bots_batch() {
    # Show menu once
    header
    while true; do
        echo -e "${YELLOW} --- Bulk Delete Bots --- ${NC}"
        
        # Array to store bot names
        bots=()
        if [ -d "$BOTS_ROOT" ]; then
            for d in "$BOTS_ROOT"/*; do
                if [ -d "$d" ]; then
                    bots+=("$(basename "$d")")
                fi
            done
        fi
        
        if [ ${#bots[@]} -eq 0 ]; then
            echo "No bots found."
            read -p "Enter to return..."
            return
        fi
        
        echo "Bots available for deletion:"
        for i in "${!bots[@]}"; do
            echo "$((i+1)). ${bots[$i]}"
        done
        echo "0. Return"
        echo ""
        echo -e "${YELLOW}Enter NUMBERS separated by SPACE (ex: 1 2 5):${NC}"
        read -p "> " bot_nums
        
        # Handle Empty (Enter key) - Just refresh
        if [[ -z "$bot_nums" ]]; then
            echo ""
            continue
        fi
        
        # Handle Return
        if [[ "$bot_nums" == "0" ]]; then return; fi
        
        # Parse and validate numbers
        selected_bots=()
        invalid=false
        for num in $bot_nums; do
            if [[ ! "$num" =~ ^[0-9]+$ ]] || [ "$num" -lt 1 ] || [ "$num" -gt "${#bots[@]}" ]; then
                echo -e "${RED}Invalid number: $num${NC}"
                invalid=true
                break
            fi
            idx=$((num-1))
            selected_bots+=("${bots[$idx]}")
        done
        
        if [ "$invalid" = true ]; then
            echo ""
            continue
        fi
        
        # Show summary and confirm
        echo ""
        echo -e "${RED}WARNING: You are about to DELETE the following bots:${NC}"
        for bot in "${selected_bots[@]}"; do
            echo "  - $bot"
        done
        echo ""
        read -p "Are you sure? (y/N): " confirm
        
        if [[ "$confirm" =~ ^[yY]$ ]]; then
            echo ""
            echo -e "${YELLOW}Stopping all selected containers...${NC}"
            # Stop all selected containers at once
            docker stop -t 1 "${selected_bots[@]}" >/dev/null 2>&1
            
            echo -e "${YELLOW}Removing containers...${NC}"
            # Remove all selected containers at once
            docker rm "${selected_bots[@]}" >/dev/null 2>&1
            
            echo -e "${YELLOW}Removing folders...${NC}"
            # Remove directories
            for bot_name in "${selected_bots[@]}"; do
                BOT_DIR="${BOTS_ROOT}/${bot_name}"
                if [ -d "$BOT_DIR" ]; then
                    rm -rf "$BOT_DIR"
                fi
            done
            
            echo ""
            echo -e "${GREEN}Bulk cleanup completed! ${#selected_bots[@]} bot(s) deleted.${NC}"
            read -p "Press Enter to continue..."
            header
        else
            echo "Cancelled."
            echo ""
        fi
    done
}

# Function: Bulk Update Configuration
bulk_update_config() {
    header
    echo -e "${YELLOW} --- Bulk Update Configuration --- ${NC}"
    echo ""
    
    # Get list of bots
    bots=()
    if [ -d "$BOTS_ROOT" ]; then
        for d in "$BOTS_ROOT"/*; do
            if [ -d "$d" ]; then
                bot_name=$(basename "$d")
                bots+=("$bot_name")
            fi
        done
    fi
    
    if [ ${#bots[@]} -eq 0 ]; then
        echo "No bots found."
        read -p "Enter to return..."
        return
    fi
    
    # Read first bot's config as reference
    first_bot="${bots[0]}"
    first_config="$BOTS_ROOT/$first_bot/config.json"
    
    if [ ! -f "$first_config" ]; then
        echo -e "${RED}Error: config.json not found.${NC}"
        read -p "Enter to return..."
        return
    fi
    
    # Extract current values
    current_host=$(jq -r '.teamtalk.hostname // "N/A"' "$first_config")
    current_tcp=$(jq -r '.teamtalk.tcp_port // "N/A"' "$first_config")
    current_udp=$(jq -r '.teamtalk.udp_port // "N/A"' "$first_config")
    current_enc=$(jq -r '.teamtalk.encrypted // false' "$first_config")
    current_user=$(jq -r '.teamtalk.username // "N/A"' "$first_config")
    current_chan=$(jq -r '.teamtalk.channel // "/"' "$first_config")
    current_chan_pass=$(jq -r '.teamtalk.channel_password // ""' "$first_config")
    
    echo -e "${GREEN}Current configuration (reference: $first_bot):${NC}"
    echo "  Server: $current_host"
    echo "  TCP: $current_tcp"
    echo "  UDP: $current_udp"
    echo "  Encryption: $([ "$current_enc" = "true" ] && echo "Yes" || echo "No")"
    echo "  Username: $current_user"
    echo "  Channel: $current_chan"
    echo "  Channel Password: $([ -n "$current_chan_pass" ] && echo "*****" || echo "(None)")"
    echo ""
    echo "Total bots: ${#bots[@]}"
    echo ""
    
    # Menu for field selection
    while true; do
        echo "What do you want to change?"
        echo "1. Server (hostname)"
        echo "2. Ports (TCP/UDP)"
        echo "3. Encryption"
        echo "4. Credentials (username/password)"
        echo "5. Channel & Password"
        echo "6. Everything"
        echo "0. Cancel"
        echo ""
        read -p "Choose an option: " choice
        
        if [[ -z "$choice" ]]; then
            echo ""
            continue
        fi
        
        case $choice in
            0)
                return
                ;;
            1|2|3|4|5|6)
                break
                ;;
            *)
                echo ""
                continue
                ;;
        esac
    done
    
    # Collect new values based on choice
    # Initialize with UNSET to distinguish between "keep current" and "clear"
    new_host="UNSET"
    new_tcp="UNSET"
    new_udp="UNSET"
    new_enc="UNSET"
    new_user="UNSET"
    new_pass="UNSET"
    new_chan="UNSET"
    new_chan_pass="UNSET"
    
    echo ""
    
    if [[ "$choice" == "1" || "$choice" == "6" ]]; then
        read -p "New server (Enter = keep): " input
        if [ -n "$input" ]; then new_host="$input"; fi
    fi
    
    if [[ "$choice" == "2" || "$choice" == "6" ]]; then
        read -p "New TCP port (Enter = keep): " input
        if [ -n "$input" ]; then new_tcp="$input"; fi
        read -p "New UDP port (Enter = keep): " input
        if [ -n "$input" ]; then new_udp="$input"; fi
    fi
    
    if [[ "$choice" == "3" || "$choice" == "6" ]]; then
        read -p "Encryption (y/N): " enc_input
        if [[ "$enc_input" =~ ^[yY]$ ]]; then
            new_enc="true"
        elif [[ "$enc_input" =~ ^[nN]$ ]]; then
            new_enc="false"
        fi
    fi
    
    if [[ "$choice" == "4" || "$choice" == "6" ]]; then
        read -p "New username (Enter = keep, '.' = clear): " input
        if [ "$input" == "." ]; then new_user=""; elif [ -n "$input" ]; then new_user="$input"; fi
        
        read -p "New password (Enter = keep, '.' = clear): " input
        if [ "$input" == "." ]; then new_pass=""; elif [ -n "$input" ]; then new_pass="$input"; fi
    fi
    
    if [[ "$choice" == "5" || "$choice" == "6" ]]; then
        read -p "New Channel (Enter = keep, '.' = root '/'): " input
        if [ "$input" == "." ]; then new_chan="/"; elif [ -n "$input" ]; then new_chan="$input"; fi
        
        read -p "New Channel Password (Enter = keep, '.' = clear): " input
        if [ "$input" == "." ]; then new_chan_pass=""; elif [ -n "$input" ]; then new_chan_pass="$input"; fi
    fi
    
    # Show summary
    echo ""
    echo -e "${YELLOW}Changes summary:${NC}"
    [ "$new_host" != "UNSET" ] && echo "  Server: $new_host"
    [ "$new_tcp" != "UNSET" ] && echo "  TCP: $new_tcp"
    [ "$new_udp" != "UNSET" ] && echo "  UDP: $new_udp"
    [ "$new_enc" != "UNSET" ] && echo "  Encryption: $([ "$new_enc" = "true" ] && echo "Yes" || echo "No")"
    
    if [ "$new_user" != "UNSET" ]; then
        if [ -z "$new_user" ]; then echo "  Username: (Cleared)"; else echo "  Username: $new_user"; fi
    fi
    
    if [ "$new_pass" != "UNSET" ]; then
        if [ -z "$new_pass" ]; then echo "  Password: (Cleared)"; else echo "  Password: ********"; fi
    fi
    
    if [ "$new_chan" != "UNSET" ]; then
        echo "  Channel: $new_chan"
    fi
    
    if [ "$new_chan_pass" != "UNSET" ]; then
        if [ -z "$new_chan_pass" ]; then echo "  Channel Password: (Cleared)"; else echo "  Channel Password: ********"; fi
    fi
    echo ""
    echo "Will be applied to ${#bots[@]} bot(s)"
    echo ""
    
    read -p "Confirm changes? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
        echo "Cancelled."
        read -p "Enter to return..."
        return
    fi
    
    # Update all bot configs
    echo ""
    echo -e "${YELLOW}Updating configurations...${NC}"
    
    for bot_name in "${bots[@]}"; do
        config_file="$BOTS_ROOT/$bot_name/config.json"
        
        if [ ! -f "$config_file" ]; then
            echo "  ⚠ Skipping $bot_name (config.json not found)"
            continue
        fi
        
        tmp_config=$(mktemp)
        
        # Build jq command dynamically
        jq_cmd="."
        
        if [ "$new_host" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.hostname = \"$new_host\""
        fi
        
        if [ "$new_tcp" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.tcp_port = $new_tcp"
        fi
        
        if [ "$new_udp" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.udp_port = $new_udp"
        fi
        
        if [ "$new_enc" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.encrypted = $new_enc"
        fi
        
        if [ "$new_user" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.username = \"$new_user\""
        fi
        
        if [ "$new_pass" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.password = \"$new_pass\""
        fi
        
        if [ "$new_chan" != "UNSET" ]; then
            jq_cmd="$jq_cmd | .teamtalk.channel = \"$new_chan\""
        fi
        
        if [ "$new_chan_pass" != "UNSET" ]; then
           jq_cmd="$jq_cmd | .teamtalk.channel_password = \"$new_chan_pass\""
        fi
        
        jq "$jq_cmd" "$config_file" > "$tmp_config" && mv "$tmp_config" "$config_file"
        
        # Fix permissions for container user
        chown 1000:1000 "$config_file"
        
        echo "  ✓ $bot_name updated"
    done
    
    echo ""
    echo -e "${YELLOW}Restarting all bots to apply changes...${NC}"
    docker stop -t 1 $(docker ps -a -q -f "label=role=ttmediabot") >/dev/null 2>&1
    docker start $(docker ps -a -q -f "label=role=ttmediabot") >/dev/null 2>&1
    
    echo ""
    echo -e "${GREEN}Configuration updated successfully!${NC}"
    read -p "Press Enter to continue..."
}

# Function: Duplicate Bot
duplicate_bot() {
    # Show menu once
    header
    while true; do
        echo -e "${YELLOW} --- Duplicate Bot --- ${NC}"
        
        # Array to store bot info
        bots=()
        bot_servers=()
        
        if [ -d "$BOTS_ROOT" ]; then
            for d in "$BOTS_ROOT"/*; do
                if [ -d "$d" ]; then
                    bot_name=$(basename "$d")
                    bots+=("$bot_name")
                    
                    # Extract server address from config.json
                    config_file="$d/config.json"
                    if [ -f "$config_file" ]; then
                        server=$(jq -r '.teamtalk.hostname // "N/A"' "$config_file" 2>/dev/null)
                        bot_servers+=("$server")
                    else
                        bot_servers+=("N/A")
                    fi
                fi
            done
        fi
        
        if [ ${#bots[@]} -eq 0 ]; then
            echo "No bots found."
            read -p "Enter to return..."
            return
        fi
        
        echo "Bots available to duplicate:"
        for i in "${!bots[@]}"; do
            echo "$((i+1)). ${bots[$i]} → ${bot_servers[$i]}"
        done
        echo "0. Return"
        echo ""
        read -p "Enter the NUMBER of the bot to DUPLICATE: " bot_num
        
        # Handle Empty (Enter key) - Just refresh
        if [[ -z "$bot_num" ]]; then
            echo ""
            continue
        fi
        
        # Handle Return
        if [[ "$bot_num" == "0" ]]; then return; fi
        
        # Validate input
        if [[ ! "$bot_num" =~ ^[0-9]+$ ]] || [ "$bot_num" -lt 1 ] || [ "$bot_num" -gt "${#bots[@]}" ]; then
            echo ""
            continue
        fi
        
        # Get source bot
        idx=$((bot_num-1))
        source_bot="${bots[$idx]}"
        SOURCE_BOT_DIR="${BOTS_ROOT}/${source_bot}"
        
        echo ""
        echo -e "${GREEN}Duplicating bot: $source_bot${NC}"
        echo ""
        
        # Ask for new base name
        read -p "Enter NEW BASE NAME for the bot(s) (Enter = default 'bot'): " new_base_name
        if [[ -z "$new_base_name" ]]; then
            new_base_name="bot"
        fi
        
        # Find highest existing number for both container names and nicknames
        highest_num=0
        base_name_exists=false
        highest_nickname_num=0
        nickname_base_exists=false
        
        
        if [ -d "$BOTS_ROOT" ]; then
            # Get source bot's server info for comparison
            source_hostname=$(jq -r '.teamtalk.hostname // ""' "$SOURCE_BOT_DIR/config.json")
            source_tcp_port=$(jq -r '.teamtalk.tcp_port // 0' "$SOURCE_BOT_DIR/config.json")
            
            for d in "$BOTS_ROOT"/*; do
                if [ -d "$d" ]; then
                    name=$(basename "$d")
                    
                    # Strictly check containers
                    if [[ "$name" == "$new_base_name" ]]; then
                        base_name_exists=true
                    elif [[ "$name" =~ ^${new_base_name}([0-9]+)$ ]]; then
                        n="${BASH_REMATCH[1]}"
                        [ "$n" -gt "$highest_num" ] && highest_num=$n
                    fi
                    
                    # Strictly check nicknames - BUT ONLY for bots on the SAME SERVER
                    config_file="$d/config.json"
                    if [ -f "$config_file" ]; then
                        # Get this bot's server info
                        existing_hostname=$(jq -r '.teamtalk.hostname // ""' "$config_file")
                        existing_tcp_port=$(jq -r '.teamtalk.tcp_port // 0' "$config_file")
                        
                        # Only check nicknames if it's the SAME server
                        if [[ "$existing_hostname" == "$source_hostname" ]] && [[ "$existing_tcp_port" == "$source_tcp_port" ]]; then
                            nick=$(jq -r '.teamtalk.nickname // ""' "$config_file")
                            if [[ "$nick" == "$new_base_name" ]]; then
                                nickname_base_exists=true
                            elif [[ "$nick" =~ ^${new_base_name}([0-9]+)$ ]]; then
                                n="${BASH_REMATCH[1]}"
                                [ "$n" -gt "$highest_nickname_num" ] && highest_nickname_num=$n
                            fi
                        fi
                    fi
                fi
            done
        fi
        
        # Ask for quantity
        read -p "How many ADDITIONAL bots to create (0 = only the base)?: " additional_bots
        if [[ ! "$additional_bots" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}Invalid quantity.${NC}"
            echo ""
            continue
        fi
        
        total_bots=$((additional_bots + 1))
        echo ""
        echo -e "${YELLOW}Creating $total_bots duplicated bot(s)...${NC}"
        
        # Simple sequential counter for naming
        if [ "$base_name_exists" == "true" ]; then
            next_container_num=$((highest_num + 1))
        else
            next_container_num=1
        fi
        
        if [ "$nickname_base_exists" == "true" ]; then
            next_nickname_num=$((highest_nickname_num + 1))
        else
            next_nickname_num=1
        fi
        
        # Track if we've used the base name yet
        container_base_used=$base_name_exists
        nickname_base_used=$nickname_base_exists
        
        # Loop to create duplicated bots
        for i in $(seq 1 $total_bots); do
            # Determine container name - always use base naming scheme
            if [ "$container_base_used" == "false" ]; then
                current_bot_name="$new_base_name"
                container_base_used=true
            else
                current_bot_name="${new_base_name}${next_container_num}"
                next_container_num=$((next_container_num + 1))
            fi

            # Determine nickname - same logic
            if [ "$nickname_base_used" == "false" ]; then
                current_nickname="$new_base_name"
                nickname_base_used=true
            else
                current_nickname="${new_base_name}${next_nickname_num}"
                next_nickname_num=$((next_nickname_num + 1))
            fi
            
            CURRENT_BOT_DIR="${BOTS_ROOT}/${current_bot_name}"
            
            # Check if container exists
            if [ "$(docker ps -a -q -f name=^/${current_bot_name}$)" ]; then
                echo -e "${RED}Skipping '$current_bot_name' (container already exists)${NC}"
                continue
            fi
            
            if [ -d "$CURRENT_BOT_DIR" ]; then
                echo -e "${RED}Skipping '$current_bot_name' (folder already exists)${NC}"
                continue
            fi
            
            echo ""
            echo -e "${YELLOW}Creating bot '$current_bot_name' (Nickname: $current_nickname)...${NC}"
            mkdir -p "$CURRENT_BOT_DIR"
            
            # Copy config from source bot
            cp "$SOURCE_BOT_DIR/config.json" "$CURRENT_BOT_DIR/config.json"
            
            # Update nickname
            tmp_config=$(mktemp)
            jq --arg nick "$current_nickname" '.teamtalk.nickname = $nick' "$CURRENT_BOT_DIR/config.json" > "$tmp_config" && mv "$tmp_config" "$CURRENT_BOT_DIR/config.json"
            
            # Copy cookies if exists
            if [ -f "$SOURCE_BOT_DIR/cookies.txt" ]; then
                cp "$SOURCE_BOT_DIR/cookies.txt" "$CURRENT_BOT_DIR/cookies.txt"
            else
                touch "$CURRENT_BOT_DIR/cookies.txt"
            fi
            
            # Fix permissions
            chown -R 1000:1000 "$CURRENT_BOT_DIR"
            
            # Create container (without starting)
            COOKIES_MOUNT_DUP="-v ${CURRENT_BOT_DIR}/cookies.txt:/home/ttbot/TTMediaBot/data/cookies.txt"
            docker create \
                --name "${current_bot_name}" \
                --network host \
                --label "role=ttmediabot" \
                --restart always \
                -v "${CURRENT_BOT_DIR}:/home/ttbot/TTMediaBot/data" \
                -v "${CURRENT_BOT_DIR}/cookies.txt:/home/ttbot/TTMediaBot/data/cookies.txt" \
                "${BOT_IMAGE}" > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo "  ✓ Bot '$current_bot_name' created"
            else
                echo "  ✗ Error creating '$current_bot_name'"
            fi
        done
        
        echo ""
        echo -e "${YELLOW}Starting all bots in parallel...${NC}"
        # Start all newly created bots in parallel
        docker start $(docker ps -a -q -f "label=role=ttmediabot" -f "status=created") 2>/dev/null
        
        echo -e "${GREEN}Duplication completed! $total_bots bot(s) created and started.${NC}"
        read -p "Press Enter to continue..."
        header
    done
}

# Function: Update Cookies for All Bots
update_all_cookies() {
    header
    echo -e "${YELLOW} --- Update Cookies for All Bots --- ${NC}"
    list_bots
    
    read -p "Path to NEW cookies file (Ex: /root/cookies.txt): " new_cookies_path
    
    if [ ! -f "$new_cookies_path" ]; then
        echo -e "${RED}File not found!${NC}"
        read -p "Enter to return..."
        return
    fi
    
    echo "Updating cookies in all bots..."
    
    # Loop verify dirs
    found_any=false
    for bot_dir in "$BOTS_ROOT"/*; do
        if [ -d "$bot_dir" ]; then
            found_any=true
            bot_name=$(basename "$bot_dir")
            echo "Updating bot: $bot_name"
            
            cp "$new_cookies_path" "$bot_dir/cookies.txt"
            
            # Ensure permissions
            chown 1000:1000 "$bot_dir/cookies.txt"
            
            echo -e "${GREEN}OK.${NC}"
        fi
    done
    
    if [ "$found_any" = false ]; then
        echo "No bots found."
    else
        echo -e "${YELLOW}Restarting all bots to apply new cookies...${NC}"
        
        # Stop all bots in parallel (fast)
        echo "Stopping bots..."
        docker stop -t 1 $(docker ps -a -q -f "label=role=ttmediabot") 2>/dev/null
        
        # Start all bots in parallel (fast)
        echo "Starting bots..."
        docker start $(docker ps -a -q -f "label=role=ttmediabot") 2>/dev/null
        
        echo -e "${GREEN}All bots restarted.${NC}"
    fi
    
    read -p "Completed. Enter to return..."
}

# Function: Restart All with Timer
restart_with_timer() {
    header
    echo -e "${YELLOW} --- Restart with Timer (Exit and Return) --- ${NC}"
    
    echo "This will STOP all bots, wait for the defined time, and START them again."
    read -p "Enter wait time in SECONDS (ex: 5): " wait_time
    
    if [[ ! "$wait_time" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Invalid time.${NC}"
        read -p "Enter to return..."
        return
    fi
    
    echo -e "${YELLOW}Stopping all bots...${NC}"
    docker stop -t 1 $(docker ps -a -q -f "label=role=ttmediabot")
    
    echo -e "${YELLOW}Waiting ${wait_time} seconds...${NC}"
    # Countdown visual
    for ((i=wait_time; i>0; i--)); do
        printf "\r%02d..." "$i"
        sleep 1
    done
    echo ""
    
    echo -e "${YELLOW}Starting all bots...${NC}"
    docker start $(docker ps -a -q -f "label=role=ttmediabot")
    
    echo -e "${GREEN}Process completed.${NC}"
    read -p "Enter to return..."
}

# Function: Full Uninstall
uninstall_all() {
    clear
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}      COMPLETE UNINSTALLATION            ${NC}"
    echo -e "${RED}=========================================${NC}"
    echo ""
    echo -e "${RED}WARNING: THIS ACTION IS DESTRUCTIVE!${NC}"
    echo "It will do the following:"
    echo "1. STOP and REMOVE all 'ttmediabot' containers."
    echo "2. REMOVE the Docker image 'ttmediabot'."
    echo "3. DELETE the '${BOTS_ROOT}' folder with all bots and configs."
    echo ""
    
    read -p "Type 'yes' to confirm total destruction: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        read -p "Enter to return..."
        return
    fi
    
    echo ""
    echo -e "${YELLOW}1. Stopping containers (forced)...${NC}"
    # Stop and remove all related containers
    docker stop -t 1 $(docker ps -a -q -f "label=role=ttmediabot") 2>/dev/null
    docker rm $(docker ps -a -q -f "label=role=ttmediabot") 2>/dev/null
    
    echo -e "${YELLOW}2. Total Nuke on Docker (Images, Networks, Volumes)...${NC}"
    docker system prune -a -f --volumes 2>/dev/null
    
    echo -e "${YELLOW}3. Stopping Docker service...${NC}"
    systemctl stop docker 2>/dev/null
    systemctl stop docker.socket 2>/dev/null
    
    echo -e "${YELLOW}4. Removing bot files...${NC}"
    if [ -d "$BOTS_ROOT" ]; then
        rm -rf "$BOTS_ROOT"
    fi
    
    echo ""
    echo -e "${YELLOW}4. Uninstalling Docker and dependencies (Total Cleanup)...${NC}"
    apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
    
    echo "Removing residual configuration folders and files..."
    sudo rm -rf /var/lib/docker
    sudo rm -rf /var/lib/containerd
    sudo rm -rf /etc/docker
    sudo rm -rf /etc/apparmor.d/docker
    sudo rm -rf /var/run/docker.sock
    sudo rm -rf /var/run/docker
    sudo rm -rf /run/docker
    sudo rm -rf /root/.docker
    sudo rm -rf /home/*/.docker
    sudo rm -rf /var/log/docker
    sudo rm -rf /var/log/containerd
    
    # Remove manual binary installs if any
    rm -f /usr/local/bin/docker-compose
    
    echo "Removing 'docker' group..."
    groupdel docker 2>/dev/null || true
    
    echo "Cleaning unused packages..."
    apt-get autoremove -y >/dev/null
    apt-get autoclean -y >/dev/null
    
    echo ""
    echo -e "${GREEN}CLEANUP COMPLETED.${NC}"
    echo "All containers, images, configurations, and Docker itself were removed from the system."
    echo -e "${YELLOW}The project folder ('$(pwd)') WAS KEPT, as requested.${NC}"
    echo -e "${RED}Recommended to restart the server to clear network interfaces (docker0).${NC}"
    exit 0
}

# Function: Manage Bots
manage_bots() {
    # Show menu once
    header
    while true; do
        echo -e "${YELLOW} --- Manage Bots --- ${NC}"
        echo "1. Start All (With label role=ttmediabot)"
        echo "2. Restart All (With label role=ttmediabot)"
        echo "3. Stop All (With label role=ttmediabot)"
        echo "4. Delete Bot"
        echo "5. Bulk Delete Bots"
        echo "6. Duplicate Bot"
        echo "7. Update Cookies (All Bots)"
        echo "8. Restart with Timer (Stop -> Wait -> Start)"
        echo "9. Bulk Update Configuration"
        echo "10. Return to Main Menu"
        echo ""
        read -p "Choose an option: " opt_manage
        
        # Handle empty input - just reprint menu
        if [ -z "$opt_manage" ]; then
            echo ""
            continue
        fi
        
        case $opt_manage in
            1)
                echo "Starting all bots..."
                docker start $(docker ps -a -q -f "label=role=ttmediabot")
                read -p "Completed. Enter to continue..."
                header
                ;;
            2)
                echo "Restarting all bots..."
                echo "  Stopping..."
                docker stop -t 1 $(docker ps -a -q -f "label=role=ttmediabot")
                echo "  Starting..."
                docker start $(docker ps -a -q -f "label=role=ttmediabot")
                read -p "Completed. Enter to continue..."
                header
                ;;
            3)
                echo "Stopping all bots..."
                docker stop -t 1 $(docker ps -a -q -f "label=role=ttmediabot")
                read -p "Completed. Enter to continue..."
                header
                ;;
            4)
                delete_bot
                header
                ;;
            5)
                delete_bots_batch
                header
                ;;
            6)
                duplicate_bot
                header
                ;;
            7)
                update_all_cookies
                header
                ;;
            8)
                restart_with_timer
                header
                ;;
            9)
                bulk_update_config
                header
                ;;
            10)
                return
                ;;
            *)
                # Invalid option - just reprint menu
                echo ""
                ;;
        esac
    done
}

# Check/Install Deps first
install_dependencies
build_image

# Main Menu
mkdir -p "$BOTS_ROOT"

# Show menu once
header
while true; do
    echo "1. Create Bot"
    echo "2. Manage Bots"
    echo "3. Rebuild Image / Update Code"
    echo "4. Uninstall Everything (Total Cleanup)"
    echo "5. Exit"
    echo ""
    read -p "Choose an option: " option
    
    # Handle empty input - just reprint menu
    if [ -z "$option" ]; then
        echo ""
        continue
    fi
    
    case $option in
        1)
            create_bot
            header
            ;;
        2)
            manage_bots
            header
            ;;
        3)
            force_rebuild_image
            header
            ;;
        4)
            uninstall_all
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            # Invalid option - just reprint menu
            echo ""
            ;;
    esac
done
