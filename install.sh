#!/bin/bash

# Insta v2.0 - Dependency Installer
# Installs required system packages for Brute.sh

set -e

RED='\e[1;91m'
GREEN='\e[1;92m'
YELLOW='\e[1;93m'
NC='\e[0m'

printf "${GREEN}[*] Insta v2.0 - Dependency Installer${NC}\n"

if [[ "$(id -u)" -ne 0 ]]; then
    printf "${RED}[!] Please run as root: sudo ./install.sh${NC}\n"
    exit 1
fi

if command -v apt-get > /dev/null 2>&1; then
    printf "${YELLOW}[*] Detected Debian/Ubuntu/Kali Linux${NC}\n"
    apt-get update -qq
    apt-get install -y tor curl openssl
elif command -v pacman > /dev/null 2>&1; then
    printf "${YELLOW}[*] Detected Arch Linux${NC}\n"
    pacman -S --noconfirm tor curl openssl
elif command -v dnf > /dev/null 2>&1; then
    printf "${YELLOW}[*] Detected Fedora/RHEL${NC}\n"
    dnf install -y tor curl openssl
elif command -v yum > /dev/null 2>&1; then
    printf "${YELLOW}[*] Detected CentOS/RHEL (legacy)${NC}\n"
    yum install -y tor curl openssl
else
    printf "${RED}[!] Could not detect package manager${NC}\n"
    printf "${RED}[!] Please install manually: tor curl openssl${NC}\n"
    exit 1
fi

printf "\n${GREEN}[+] All dependencies installed successfully!${NC}\n"
printf "${GREEN}[*] Run: sudo ./Brute.sh${NC}\n"
