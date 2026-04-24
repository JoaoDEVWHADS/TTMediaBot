#!/bin/bash

# masc.sh - TTMediaBot Auto-Update Controller
# This script manages the masking and activation of the auto-updater service.

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVICE_NAME="ttmediabot-updater.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
BACKUP_PATH="/etc/systemd/system/$SERVICE_NAME.bak"

header() {
    clear
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}      TTMediaBot Auto-Update Manager     ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
}

enable_auto_update() {
    echo -e "${YELLOW}Enabling Auto-Updates...${NC}"
    
    # 1. Restore service file if backup exists
    if [ -f "$BACKUP_PATH" ]; then
        echo "Restoring service file from backup..."
        mv -f "$BACKUP_PATH" "$SERVICE_PATH"
    fi
    
    # 2. Unmask, reload, enable, and start
    systemctl unmask "$SERVICE_NAME"
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    echo -e "${GREEN}Auto-Updates enabled successfully!${NC}"
    sleep 2
}

disable_auto_update() {
    echo -e "${YELLOW}Disabling Auto-Updates...${NC}"
    
    # 1. Stop and disable
    systemctl stop "$SERVICE_NAME"
    systemctl disable "$SERVICE_NAME"
    
    # 2. Backup service file to allow masking if it's a regular file
    if [ -f "$SERVICE_PATH" ] && [ ! -L "$SERVICE_PATH" ]; then
        echo "Backing up service file..."
        mv -f "$SERVICE_PATH" "$BACKUP_PATH"
    fi
    
    # 3. Reload and mask
    systemctl daemon-reload
    systemctl mask "$SERVICE_NAME"
    
    echo -e "${GREEN}Auto-Updates disabled and masked successfully!${NC}"
    sleep 2
}

while true; do
    header
    echo "Current Status:"
    systemctl is-active --quiet "$SERVICE_NAME" && echo -e "  Service: ${GREEN}Active${NC}" || echo -e "  Service: ${RED}Inactive${NC}"
    systemctl is-enabled --quiet "$SERVICE_NAME" && echo -e "  Enabled: ${GREEN}Yes${NC}" || echo -e "  Enabled: ${RED}No${NC}"
    [ -L "$SERVICE_PATH" ] && [ "$(readlink -f $SERVICE_PATH)" == "/dev/null" ] && echo -e "  Masked:  ${RED}Yes${NC}" || echo -e "  Masked:  ${GREEN}No${NC}"
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
