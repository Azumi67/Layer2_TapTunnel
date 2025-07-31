#!/bin/bash

RED="\033[91m"
GREEN="\033[92m"
YELLOW="\033[93m"
BLUE="\033[94m"
CYAN="\033[96m"
RESET="\033[0m"
apt update -y
apt install wget -y
echo -e "${GREEN}Downloading logo ...${RESET}"
wget -O /etc/logo2.sh https://github.com/Azumi67/UDP2RAW_FEC/raw/main/logo2.sh
chmod +x /etc/logo2.sh
if [ -f "tap.py" ]; then
    echo -e "${YELLOW}Removing existing tap.py ...${RESET}"
    rm tap.py
fi
echo -e "${YELLOW}Downloading tap.py...${RESET}"
wget https://github.com/Azumi67/Layer2_TapTunnel/releases/download/V1.0/tap.py
echo -e "${GREEN}Launching tap.py...${RESET}"
python3 tap.py
