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
    cd "$DIR_NAME" || exit
    echo "--- Setting Permissions ---"
    chmod +x *.sh ./ttbotdocker.sh
    
    echo "========================================="
    echo "Setup Complete! Starting Docker Manager..."
    echo "========================================="
    sleep 2
    exec ./ttbotdocker.sh
else
    echo "Error: Directory not found after clone."
    exit 1
fi
