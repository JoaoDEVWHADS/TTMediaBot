#!/bin/bash

# ================================================================= #
# Automated Installation Script - TTMediaBot
# Adjusted for execution from within the bot directory
# ================================================================= #

# Navigating to the parent directory to begin installation
echo "--- Exiting bot directory to configure environment in parent folder ---"
cd ..

echo "--- Detecting package manager and installing dependencies ---"
ARCH=$(uname -m)

# Package mappings and installation based on package manager
if command -v apt-get &> /dev/null; then
    EXTRA_PACKAGES=""
    if [[ "$ARCH" == "aarch64" || "$ARCH" =~ ^arm ]]; then
        EXTRA_PACKAGES="libportaudio2"
    fi
    sudo apt-get update -y
    sudo apt-get install -y libmpv-dev pulseaudio p7zip-full python3-venv git python3-pip ca-certificates curl gnupg $EXTRA_PACKAGES

    # Node.js LTS Installation via NodeSource for APT
    echo "--- Configuring Node.js LTS Repository ---"
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs

elif command -v dnf &> /dev/null; then
    EXTRA_PACKAGES=""
    if [[ "$ARCH" == "aarch64" || "$ARCH" =~ ^arm ]]; then
        EXTRA_PACKAGES="portaudio"
    fi
    sudo dnf install -y mpv-devel pulseaudio p7zip python3 git python3-pip ca-certificates curl gnupg2 nodejs $EXTRA_PACKAGES

elif command -v yum &> /dev/null; then
    EXTRA_PACKAGES=""
    if [[ "$ARCH" == "aarch64" || "$ARCH" =~ ^arm ]]; then
        EXTRA_PACKAGES="portaudio"
    fi
    sudo yum install -y epel-release || true
    sudo yum install -y mpv-devel pulseaudio p7zip python3 git python3-pip ca-certificates curl gnupg2 nodejs $EXTRA_PACKAGES

elif command -v pacman &> /dev/null; then
    EXTRA_PACKAGES=""
    if [[ "$ARCH" == "aarch64" || "$ARCH" =~ ^arm ]]; then
        EXTRA_PACKAGES="portaudio"
    fi
    sudo pacman -Sy --noconfirm mpv pulseaudio p7zip python git python-pip ca-certificates curl gnupg nodejs $EXTRA_PACKAGES

elif command -v zypper &> /dev/null; then
    EXTRA_PACKAGES=""
    if [[ "$ARCH" == "aarch64" || "$ARCH" =~ ^arm ]]; then
        EXTRA_PACKAGES="portaudio"
    fi
    sudo zypper install -y mpv-devel pulseaudio p7zip python3 git python3-pip ca-certificates curl gpg2 nodejs $EXTRA_PACKAGES

elif command -v apk &> /dev/null; then
    EXTRA_PACKAGES=""
    if [[ "$ARCH" == "aarch64" || "$ARCH" =~ ^arm ]]; then
        EXTRA_PACKAGES="portaudio"
    fi
    sudo apk add --no-cache mpv-dev pulseaudio p7zip python3 git py3-pip ca-certificates curl gnupg nodejs $EXTRA_PACKAGES

else
    echo "Error: Unsupported package manager. Please install dependencies manually."
    exit 1
fi

# Python Environment Setup in the parent directory
echo "--- Creating and activating virtual environment (venv) ---"
python3 -m venv venv

# Activate venv for the current script session
source venv/bin/activate

# Return to bot directory to install Python requirements
if [ -d "TTMediaBot" ]; then
    cd TTMediaBot
    echo "--- Installing requirements and specific dependencies within venv ---"
    
    # Ensure pip is up to date inside venv
    pip install --upgrade pip

    # Install project libraries
    pip3 install -r requirements.txt

    # Update yt-dlp to the pre-release version
    pip install -U --pre "yt-dlp[default]"

    # Adjust httpx version
    echo "--- Adjusting httpx version ---"
    pip uninstall -y httpx
    pip install httpx==0.27.0

    # Final permission adjustment
    echo "--- Applying 775 permissions to files ---"
    git config core.fileMode false 2>/dev/null
    chmod -R 775 .

    echo "---------------------------------------------------------------------"
    echo "INSTALLATION COMPLETED SUCCESSFULLY"
    echo "---------------------------------------------------------------------"
    echo "IMPORTANT INSTRUCTIONS:"
    echo "1. Please configure the 'config.json' file with your server details"
    echo "   and the correct path for your cookies."
    echo ""
    echo "2. The virtual environment (venv) is currently ACTIVE in this session."
    echo ""
    echo "3. If you close this terminal and need to reactivate the environment,"
    echo "   run the following command from the parent directory:"
    echo "   source venv/bin/activate"
    echo "---------------------------------------------------------------------"

    # Maintain the shell in the virtual environment
    exec bash --rcfile <(echo "source ~/.bashrc; source ../venv/bin/activate")

else
    echo "--- Error: TTMediaBot directory not found upon return! ---"
    exit 1
fi
