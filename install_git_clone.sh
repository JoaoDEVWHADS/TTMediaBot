#!/bin/bash

# ================================================================= #
# Auto Installer & Cloner - TTMediaBot
# ================================================================= #

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

echo "--- Checking for Git ---"
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing..."
    apt-get update && apt-get install -y git
else
    echo "Git is already installed."
fi

echo "--- Checking for unzip (ZIP extractor) ---"
if ! command -v unzip &> /dev/null; then
    echo "unzip not found. Installing..."
    apt-get install -y unzip
else
    echo "unzip is already installed."
fi

# Clone the repository
REPO_URL="https://github.com/JoaoDEVWHADS/TTMediaBot"
DIR_NAME="TTMediaBot"

if [ -d "$DIR_NAME" ]; then
    echo "Directory '$DIR_NAME' already exists. Skipping clone."
    echo "Consider deleting it if you want a fresh install: rm -rf $DIR_NAME"
else
    echo "--- Cloning Repository ---"
    git clone "$REPO_URL"
    if [ $? -ne 0 ]; then
        echo "Error cloning repository. Check your internet connection."
        exit 1
    fi
fi

# Enter directory and set permissions
if [ -d "$DIR_NAME" ]; then
    echo "--- Setting Permissions and Ownership ---"
    
    REAL_USER=${SUDO_USER:-$USER}
    
    chown -R "$REAL_USER":"$REAL_USER" "$DIR_NAME"
    chmod -R 777 "$DIR_NAME"
    chmod +x "$DIR_NAME"/*.sh
    
    echo "Ownership and permissions set for user: $REAL_USER"
    
    cd "$DIR_NAME" || exit
    
    echo "========================================="
    echo "--- Downloading TeamTalk_DLL.zip ---"
    echo "========================================="
    
    DLL_URL="https://github.com/JoaoDEVWHADS/TTMediaBot/releases/download/downloadttdll/TeamTalk_DLL.zip"
    DLL_FILE="TeamTalk_DLL.zip"
    
    if [ -f "$DLL_FILE" ]; then
        echo "TeamTalk_DLL.zip already exists. Skipping download."
    else
        wget "$DLL_URL" -O "$DLL_FILE"
        if [ $? -ne 0 ]; then
            echo "Error downloading TeamTalk_DLL.zip. Check your internet connection."
            exit 1
        fi
        echo "Download complete!"
    fi
    
    echo "========================================="
    echo "--- Extracting TeamTalk_DLL.zip ---"
    echo "========================================="
    
    unzip -o "$DLL_FILE"
    if [ $? -ne 0 ]; then
        echo "Error extracting TeamTalk_DLL.zip."
        exit 1
    fi
    echo "Extraction complete!"
    
    echo "--- Removing TeamTalk_DLL.zip ---"
    rm -f "$DLL_FILE"
    echo "ZIP file removed."
    
    echo "========================================="
    echo "--- Verifying TeamTalk_DLL folder ---"
    echo "========================================="
    
    if [ ! -d "TeamTalk_DLL" ]; then
        echo "ERROR: TeamTalk_DLL folder not found after extraction!"
        exit 1
    fi
    echo "TeamTalk_DLL folder found!"
    
    echo "--- Setting permissions for TeamTalk_DLL ---"
    chown -R "$REAL_USER":"$REAL_USER" TeamTalk_DLL
    chmod -R 777 TeamTalk_DLL
    echo "Permissions set for TeamTalk_DLL folder."
    
    echo "========================================="
    echo "--- Final Verification ---"
    echo "========================================="
    
    ls -la | grep TeamTalk_DLL
    
    if [ -d "TeamTalk_DLL" ] && [ "$(stat -c '%U' TeamTalk_DLL)" = "$REAL_USER" ]; then
        echo "? All checks passed!"
        echo "? TeamTalk_DLL folder exists"
        echo "? Ownership is correct: $REAL_USER"
        echo "? Permissions are set to 777"
        echo "========================================="
        echo "--- Checking Docker Installation ---"
        echo "========================================="

        # =========================================
        # DOCKER AUTO FIX (ONLY ADDITION MADE)
        # =========================================

        if ! command -v docker &> /dev/null; then
            echo "Docker not found. Installing automatically..."
            curl -fsSL https://get.docker.com | sh
        else
            echo "Docker is already installed."
        fi

        echo "--- Ensuring Docker service is running ---"
        systemctl enable docker
        systemctl start docker

        if ! systemctl is-active --quiet docker; then
            echo "Docker service failed to start."
            exit 1
        fi

        echo "--- Adding user to docker group ---"
        usermod -aG docker "$REAL_USER"

        echo "Docker is ready."
        echo "========================================="
        echo "Setup Complete! Starting Docker Manager..."
        echo "========================================="
        sleep 2

        exec ./ttbotdocker.sh
    else
        echo "ERROR: Verification failed. Please check manually."
        exit 1
    fi
else
    echo "Error: Directory not found after clone."
    exit 1
fi