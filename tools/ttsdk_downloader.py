#!/usr/bin/env python3

import patoolib
import requests

import os
import platform
import shutil
import sys

path = os.path.dirname(os.path.realpath(__file__))
path = os.path.dirname(path)
sys.path.append(path)
import downloader


url = "https://bearware.dk/teamtalksdk"



def get_url_suffix_from_platform() -> str:
    machine = platform.machine()
    if sys.platform == "win32":
        architecture = platform.architecture()
        if machine == "AMD64" or machine == "x86":
            if architecture[0] == "64bit":
                return "win64"
            else:
                return "win32"
        else:
            sys.exit("Native Windows on ARM is not supported")
    elif sys.platform == "darwin":
        sys.exit("Darwin is not supported")
    elif sys.platform.startswith("linux"):
        machine = platform.machine()
        if machine == "AMD64" or machine == "x86_64":
            # Debian 11/12 are compatible with the Ubuntu 22 build of the SDK
            return "ubuntu22_x86_64"
        elif "arm" in machine or "aarch64" in machine:
            return "raspbian_armhf"
        else:
            sys.exit(f"Your architecture ({machine}) is not supported on Linux")
    else:
        sys.exit(f"Your platform ({sys.platform}) is not supported")


def download() -> None:
    # Hardcoded version to prevent scraping errors
    version = "v5.15.0"
    base_url = "https://bearware.dk/teamtalksdk"
    
    # Determine platform suffix
    suffix = get_url_suffix_from_platform()
    
    download_url = f"{base_url}/{version}/tt5sdk_{version}_{suffix}.7z"
    
    print("Downloading from " + download_url)
    downloader.download_file(download_url, os.path.join(os.getcwd(), "ttsdk.7z"))


def extract() -> None:
    try:
        os.mkdir(os.path.join(os.getcwd(), "ttsdk"))
    except FileExistsError:
        shutil.rmtree(os.path.join(os.getcwd(), "ttsdk"))
        os.mkdir(os.path.join(os.getcwd(), "ttsdk"))
    patoolib.extract_archive(
        os.path.join(os.getcwd(), "ttsdk.7z"), outdir=os.path.join(os.getcwd(), "ttsdk")
    )

def move() -> None:
    path = os.path.join(os.getcwd(), "ttsdk", os.listdir(os.path.join(os.getcwd(), "ttsdk"))[0])
    libraries = ["TeamTalk_DLL", "TeamTalkPy"]
    # Dentro do Docker, o script é rodado como `python tools/ttsdk_downloader.py`. 
    # O CWD (Current Working Directory) é /home/ttbot/TTMediaBot (definido no WORKDIR).
    # Portanto, queremos que as pastas fiquem no CWD, não no diretório pai.
    # O script original tenta adivinhar se está em 'tools' ou não, mas no Docker isso pode confundir.
    
    # Se o script for rodado da raiz (como fazemos no Dockerfile), os arquivos devem ficar na raiz.
    dest_dir = os.getcwd()
    for library in libraries:
        try:
            os.rename(
                os.path.join(path, "Library", library), os.path.join(dest_dir, library)
            )
        except OSError:
            shutil.rmtree(os.path.join(dest_dir, library))
            os.rename(
                os.path.join(path, "Library", library), os.path.join(dest_dir, library)
            )
    try:
        os.rename(
            os.path.join(path, "License.txt"), os.path.join(dest_dir, "TTSDK_license.txt")
        )
    except FileExistsError:
        os.remove(os.path.join(dest_dir, "TTSDK_license.txt"))
        os.rename(
            os.path.join(path, "License.txt"), os.path.join(dest_dir, "TTSDK_license.txt")
        )


def clean() -> None:
    os.remove(os.path.join(os.getcwd(), "ttsdk.7z"))
    shutil.rmtree(os.path.join(os.getcwd(), "ttsdk"))


def check_local_files() -> bool:
    """Check if SDK files already exist in the user's directory."""
    required = ["TeamTalk_DLL", "TeamTalkPy"]
    # We check in the current working directory, which is where we expect them in Docker
    cwd = os.getcwd()
    missing = [f for f in required if not os.path.exists(os.path.join(cwd, f))]
    
    if not missing:
        print("SDK files found locally. Skipping download.")
        return True
    return False

def install() -> None:
    print("Installing TeamTalk sdk components")
    
    try:
        print("Downloading latest sdk version")
        download()
        print("Downloaded. extracting")
        extract()
        print("Extracted. moving")
        move()
        print("moved. cleaning")
        clean()
        print("cleaned.")
        print("Installed, exiting.")
    except Exception as e:
        print(f"Download or extraction failed: {e}")
        print("Checking for local backup files...")
        if check_local_files():
            print("Local files are present. Build can proceed using cached SDK.")
            sys.exit(0) # Success (0) because we have the files
        else:
            print("No local files found. Installation failed.")
            sys.exit(1) # Fail (1) because we have nothing

if __name__ == "__main__":
    install()
