#!/bin/bash

# masc.sh - TTMediaBot Auto-Update Controller
# This script manages the masking and activation of the auto-updater service.

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVICE_NAME="ttmediabot-updater.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Template to ensure we can always restore the service
SERVICE_TEMPLATE="[Unit]
Description=TTMediaBot Auto-Updater Watcher
After=network.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=/bin/bash $SCRIPT_DIR/auto_updater.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target"

header() {
    clear
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}      TTMediaBot Auto-Update Manager     ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
}

get_status() {
    # Use LANG=C to ensure English output for status checks
    local enabled_status=$(LANG=C systemctl is-enabled "$SERVICE_NAME" 2>/dev/null)
    local active_status=$(LANG=C systemctl is-active "$SERVICE_NAME" 2>/dev/null)

    # Check if masked
    if [[ "$enabled_status" == "masked" ]]; then
        echo -e "  Masked:  ${RED}Yes (Disabled)${NC}"
    else
        echo -e "  Masked:  ${GREEN}No (Allowed)${NC}"
    fi

    # Check if enabled
    if [ "$enabled_status" == "enabled" ]; then
        echo -e "  Enabled: ${GREEN}Yes${NC}"
    else
        echo -e "  Enabled: ${RED}No${NC}"
    fi

    # Check if active
    if [ "$active_status" == "active" ]; then
        echo -e "  Service: ${GREEN}Active (Running)${NC}"
    elif [ "$active_status" == "activating" ]; then
        echo -e "  Service: ${YELLOW}Activating...${NC}"
    else
        echo -e "  Service: ${RED}Inactive (Stopped)${NC}"
    fi
}

enable_auto_update() {
    echo -e "${YELLOW}Enabling Auto-Updates...${NC}"
    
    # 1. Unmask
    systemctl unmask "$SERVICE_NAME"
    
    # 2. Recreate service file from template
    echo "Creating service file..."
    echo "$SERVICE_TEMPLATE" > "$SERVICE_PATH"
    chmod 644 "$SERVICE_PATH"
    
    # 3. Reload, enable, and start
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    
    echo -e "${GREEN}Auto-Updates enabled!${NC}"
    sleep 2
}

disable_auto_update() {
    echo -e "${YELLOW}Disabling Auto-Updates...${NC}"
    
    # 1. Aggressive process cleanup first to prevent systemctl hang
    echo "Cleaning up processes..."
    killall -9 auto_updater.sh sleep 2>/dev/null
    
    # 2. Stop and disable (non-blocking)
    systemctl stop --no-block "$SERVICE_NAME"
    systemctl disable "$SERVICE_NAME"
    
    # 3. Remove the service file or symlink
    rm -f "$SERVICE_PATH"
    
    # 4. Mask and reload
    systemctl mask "$SERVICE_NAME"
    systemctl daemon-reload
    systemctl reset-failed "$SERVICE_NAME"
    
    echo -e "${GREEN}Auto-Updates disabled and masked!${NC}"
    sleep 2
}

while true; do
    header
    echo "Current Status:"
    get_status
    echo ""
    echo "1. Enable Auto-Updates"
    echo "2. Disable Auto-Updates"
    echo "3. Return to Main Menu"
    echo ""
    read -p "Choose an option: " choice
    
    case $choice in
        1)
            enable_auto_update
            ;;
        2)
            disable_auto_update
            ;;
        3)
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option.${NC}"
            sleep 1
            ;;
    esac
done
