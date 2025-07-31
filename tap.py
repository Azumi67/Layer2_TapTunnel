#!/usr/bin/env python3
#Author: https://github.com/Azumi67
import os
import sys
import subprocess
import getpass
import time
import re
import io
import readline

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", errors="replace")

NC = '\033[0m'
MENU = '\033[1;36m'
INPUT = '\033[1;33m'
SUCCESS = '\033[1;32m'
ERROR = '\033[1;31m'
OPTION = '\033[1;34m'
CHECK = '✔'

SERVICE_NAME = 'layer2-tap.service'
SERVICE_PATH = f'/etc/systemd/system/{SERVICE_NAME}'
KEEPALIVE_SCRIPT_PATH = '/etc/layer2-tap-keepalive.sh'
KEEPALIVE_SERVICE_NAME = 'layer2-tap-keepalive.service'
KEEPALIVE_SERVICE_PATH = f'/etc/systemd/system/{KEEPALIVE_SERVICE_NAME}'
RESET_SCRIPT_PATH = '/etc/layer2-tap-reset.sh'
CONFIG_PATH = '/etc/layer2-tap.conf'

def logo():
    logo_path = "/etc/logo2.sh"
    try:
        subprocess.run(["bash", "-c", logo_path], check=True)
    except subprocess.CalledProcessError as e:
        return e
    return None

def run(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{ERROR}✖ Command '{' '.join(cmd)}' with code {e.returncode} failed.{NC}")


def pause():
    input(f"{INPUT}Press [Enter] to continue...{NC}")

def root():
    if os.geteuid() != 0:
        print(f"{ERROR}✖ Plz run as root.{NC}")
        sys.exit(1)

def load_config():
    cfg = {
        'ROLE': '', 'DEV': '', 'LOCAL': '',
        'PORT': '', 'REMOTE': '',
        'KEEPALIVE': '', 'TIMER': ''
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                if k in cfg:
                    cfg[k] = v
    return cfg

def save_config(cfg):
    with open(CONFIG_PATH, 'w') as f:
        for key in ['ROLE', 'DEV', 'LOCAL', 'PORT', 'REMOTE', 'KEEPALIVE', 'TIMER']:
            f.write(f"{key}={cfg.get(key, '')}\n")
    print(f"{SUCCESS}{CHECK} Config saved.{NC}")

def serviceFile(exec_start, first_time=False):
    service = f"""[Unit]
Description=Layer-2 TAP tunnel
After=network.target

[Service]
Type=simple
Restart=on-failure
ExecStart={exec_start}

[Install]
WantedBy=multi-user.target
"""
    with open(SERVICE_PATH, 'w') as f:
        f.write(service)
    run(['systemctl', 'daemon-reload'])
    if first_time:
        run(['systemctl', 'enable', SERVICE_NAME])
        run(['systemctl', 'start', SERVICE_NAME])
        print(f"{SUCCESS}{CHECK} Service started.{NC}")
    else:
        run(['systemctl', 'restart', SERVICE_NAME])
        print(f"{SUCCESS}{CHECK} Service restarted.{NC}")

def kaScript(cfg):
    script = f"""#!/usr/bin/env bash
while true; do
    /usr/bin/ping -I {cfg['DEV']} -c 3 {cfg['KEEPALIVE']}
    sleep 10
done
"""
    with open(KEEPALIVE_SCRIPT_PATH, 'w') as f:
        f.write(script)
    os.chmod(KEEPALIVE_SCRIPT_PATH, 0o755)


def kaliveServiceFile(cfg, first_time=False):
    kaScript(cfg)
    service = f"""[Unit]
Description=Layer-2 TAP keepalive daemon
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash {KEEPALIVE_SCRIPT_PATH}
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
"""
    with open(KEEPALIVE_SERVICE_PATH, 'w') as f:
        f.write(service)
    run(['systemctl', 'daemon-reload'])
    if first_time:
        run(['systemctl', 'enable', KEEPALIVE_SERVICE_NAME])
        run(['systemctl', 'start', KEEPALIVE_SERVICE_NAME])
        print(f"{SUCCESS}{CHECK} Keepalive service started using custom script.{NC}")
    else:
        run(['systemctl', 'restart', KEEPALIVE_SERVICE_NAME])
        print(f"{SUCCESS}{CHECK} Keepalive service restarted using custom script.{NC}")

def reset_bash(cfg):
    if not cfg.get('TIMER'):
        return
    multiplier = 3600 if cfg['TIMER'].endswith('h') else 60
    seconds = int(cfg['TIMER'][:-1]) * multiplier
    with open(RESET_SCRIPT_PATH, 'w') as f:
        f.write(f"#!/bin/bash\nsleep {seconds}\nsystemctl restart {SERVICE_NAME}\n")
    os.chmod(RESET_SCRIPT_PATH, 0o755)
    subprocess.Popen([RESET_SCRIPT_PATH])
    print(f"{SUCCESS}{CHECK} Reset timer set: will restart in {cfg['TIMER']}.{NC}")

def install_stuff():
    os.system("clear")
    run(['apt', 'update'])
    run(['apt', 'install', '-y', 'socat'])
    run(['modprobe', 'tun'])
    print(f"{SUCCESS}{CHECK} Requirements installed.{NC}")
    pause()

def keepalive_ip(local_cidr):
    ip, _ = local_cidr.split('/', 1)
    parts = ip.split('.')
    last = int(parts[-1])
    other = 1 if last == 2 else 2
    parts[-1] = str(other)
    return '.'.join(parts)

def install_server():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mServer \033[93mMenu\033[0m")
    print('\033[92m "-"\033[93m' + "═"*50 + '\033[0m')
    cfg = {'ROLE': 'server'}
    cfg['DEV'] = input(f"{INPUT}Enter {SUCCESS}TAP device name {NC}[e.g. tap2]:{NC} ") or 'tap0'
    cfg['LOCAL'] = input(f"{INPUT}Enter {SUCCESS}local IP/mask {NC}[e.g. 192.168.200.1/24]:{NC} ") or '192.168.200.1/24'
    cfg['PORT'] = input(f"{INPUT}Enter {SUCCESS}UDP listen port {NC}[e.g. 4444]:{NC} ")
    cfg['REMOTE'] = ''
    cfg['KEEPALIVE'] = keepalive_ip(cfg['LOCAL'])
    cfg['TIMER'] = ''
    user = os.getenv('SUDO_USER') or getpass.getuser()

    run(['ip', 'tuntap', 'add', 'dev', cfg['DEV'], 'mode', 'tap', 'user', user])
    run(['ip', 'link', 'set', cfg['DEV'], 'up'])
    run(['ip', 'addr', 'add', cfg['LOCAL'], 'dev', cfg['DEV']])

    save_config(cfg)
    exec_start = f"/usr/bin/socat -d -d UDP4-LISTEN:{cfg['PORT']},reuseaddr TUN:{cfg['LOCAL']},tun-name={cfg['DEV']},tun-type=tap,iff-no-pi,iff-up"
    serviceFile(exec_start, first_time=True)
    kaliveServiceFile(cfg, first_time=True)
    reset_bash(cfg)
    pause()

def install_client():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mClient \033[93mMenu\033[0m")
    print('\033[92m "-"\033[93m' + "═"*50 + '\033[0m')
    cfg = {'ROLE': 'client'}
    cfg['DEV'] = input(f"{INPUT}Enter {SUCCESS}TAP device name {NC}[e.g. tap2]:{NC} ") or 'tap0'
    cfg['LOCAL'] = input(f"{INPUT}Enter {SUCCESS}local IP/mask {NC}[e.g. 192.168.200.2/24]:{NC} ") or '192.168.200.2/24'
    cfg['REMOTE'] = input(f"{INPUT}Enter {SUCCESS}remote Server IP{NC}:{NC} ")
    cfg['PORT'] = input(f"{INPUT}Enter {SUCCESS}UDP port {NC}[e.g. 4444]:{NC} ")
    cfg['KEEPALIVE'] = keepalive_ip(cfg['LOCAL'])
    cfg['TIMER'] = ''
    user = os.getenv('SUDO_USER') or getpass.getuser()

    run(['ip', 'tuntap', 'add', 'dev', cfg['DEV'], 'mode', 'tap', 'user', user])
    run(['ip', 'link', 'set', cfg['DEV'], 'up'])
    run(['ip', 'addr', 'add', cfg['LOCAL'], 'dev', cfg['DEV']])

    save_config(cfg)
    exec_start = f"/usr/bin/socat -d -d UDP4:{cfg['REMOTE']}:{cfg['PORT']} TUN:{cfg['LOCAL']},tun-name={cfg['DEV']},tun-type=tap,iff-no-pi,iff-up"
    serviceFile(exec_start, first_time=True)
    kaliveServiceFile(cfg, first_time=True)
    reset_bash(cfg)
    pause()

def update_config(cfg):
    if cfg['ROLE'] == 'server':
        exec_start = f"/usr/bin/socat -d -d UDP4-LISTEN:{cfg['PORT']},reuseaddr TUN:{cfg['LOCAL']},tun-name={cfg['DEV']},tun-type=tap,iff-no-pi,iff-up"
    else:
        exec_start = f"/usr/bin/socat -d -d UDP4:{cfg['REMOTE']}:{cfg['PORT']} TUN:{cfg['LOCAL']},tun-name={cfg['DEV']},tun-type=tap,iff-no-pi,iff-up"
    serviceFile(exec_start, first_time=False)
    kaliveServiceFile(cfg, first_time=False)
    reset_bash(cfg)

def edit_stuff():
    cfg = load_config()
    if not cfg['ROLE']:
        print(f"{ERROR}✖ No config found.{NC}")
        pause()
        return

    while True:
        os.system("clear")
        print("\033[92m ^ ^\033[0m")
        print("\033[92m(\033[91mO,O\033[92m)\033[0m")
        print("\033[92m(   ) \033[93mEdit \033[93mMenu\033[0m")
        print('\033[92m "-"\033[93m' + "═"*50 + '\033[0m')
        print(f"{OPTION}1) ROLE       [{cfg['ROLE']}] {NC}")
        print(f"{OPTION}2) DEV        [{cfg['DEV']}] {NC}")
        print(f"{OPTION}3) LOCAL      [{cfg['LOCAL']}] {NC}")
        print(f"{OPTION}4) PORT       [{cfg['PORT']}] {NC}")

        idx = 4
        if cfg['ROLE'] == 'client':
            client_opt = idx + 1
            print(f"{OPTION}{client_opt}) REMOTE     [{cfg['REMOTE']}] {NC}")
            idx = client_opt

        keepalive_opt = idx + 1
        print(f"{OPTION}{keepalive_opt}) KEEPALIVE  [{cfg['KEEPALIVE']}] {NC}")
        idx = keepalive_opt

        timer_opt = idx + 1
        print(f"{OPTION}{timer_opt}) TIMER      [{cfg['TIMER'] or 'none'}] {NC}")
        idx = timer_opt

        save_opt = idx + 1
        cancel_opt = idx + 2
        print(f"{SUCCESS}{CHECK} {save_opt}) Save & Restart{NC}")
        print(f"{ERROR}✖ {cancel_opt}) Cancel{NC}")

        choice = input(f"{INPUT}Choose [1-{cancel_opt}]:{NC} ")
        if choice == '1':
            cfg['ROLE'] = input(f"{INPUT}Enter ROLE (server/client) [{cfg['ROLE']}]:{NC}") or cfg['ROLE']
        elif choice == '2':
            cfg['DEV'] = input(f"{INPUT}Enter TAP device name [{cfg['DEV']}]:{NC}") or cfg['DEV']
        elif choice == '3':
            cfg['LOCAL'] = input(f"{INPUT}Enter local IP/mask [{cfg['LOCAL']}]:{NC}") or cfg['LOCAL']
            cfg['KEEPALIVE'] = keepalive_ip(cfg['LOCAL'])
        elif choice == '4':
            cfg['PORT'] = input(f"{INPUT}Enter UDP port [{cfg['PORT']}]:{NC}") or cfg['PORT']
        elif cfg['ROLE'] == 'client' and choice == str(client_opt):
            cfg['REMOTE'] = input(f"{INPUT}Enter remote server IP [{cfg['REMOTE']}]:{NC}") or cfg['REMOTE']
        elif choice == str(keepalive_opt):
            cfg['KEEPALIVE'] = input(f"{INPUT}Enter keepalive IP [{cfg['KEEPALIVE']}]:{NC}") or cfg['KEEPALIVE']
        elif choice == str(timer_opt):
            cfg['TIMER'] = input(f"{INPUT}Enter reset timer (e.g. 30m or 2h) [{cfg['TIMER']}]:{NC}") or cfg['TIMER']
        elif choice == str(save_opt):
            save_config(cfg)
            run(['ip', 'addr', 'flush', 'dev', cfg['DEV']])
            run(['ip', 'addr', 'add', cfg['LOCAL'], 'dev', cfg['DEV']])
            update_config(cfg)
            break
        elif choice == str(cancel_opt):
            break
        else:
            print(f"{ERROR}✖ Wrong choice.{NC}")
            time.sleep(1)
    pause()

def reset_timer():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mReset Timer\033[0m")
    print('\033[92m "-"\033[93m' + "═"*50 + '\033[0m')
    cfg = load_config()
    timer = input(f"{INPUT}Enter {SUCCESS}reset timer {NC}(e.g. 10m or 2h):{NC} ")
    cfg['TIMER'] = timer
    save_config(cfg)
    reset_bash(cfg)
    pause()

def uninstall():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mUninstall \033[93mMenu\033[0m")
    print('\033[92m \033[93m' + "═"*50 + '\033[0m')
    cfg = load_config()
    dev = cfg.get('DEV') or 'tap0'
    run(['systemctl','stop',SERVICE_NAME])
    run(['systemctl','disable',SERVICE_NAME])
    run(['systemctl','stop',KEEPALIVE_SERVICE_NAME])
    run(['systemctl','disable',KEEPALIVE_SERVICE_NAME])
    for p in (SERVICE_PATH, KEEPALIVE_SERVICE_PATH, RESET_SCRIPT_PATH, CONFIG_PATH):
        try: os.remove(p)
        except FileNotFoundError: pass
    run(['systemctl','daemon-reload'])
    try: run(['ip','link','del',dev])
    except: pass
    run(['apt','purge','-y','socat'])
    print(f"{SUCCESS}{CHECK} Uninstalled.{NC}")
    pause()

def status():
    os.system("clear")
    print("\033[92m ^ ^\033[0m")
    print("\033[92m(\033[91mO,O\033[92m)\033[0m")
    print("\033[92m(   ) \033[93mStatus \033[93mMenu\033[0m")
    print('\033[92m "-"\033[93m' + "═"*50 + '\033[0m')
    run(['systemctl', 'status', SERVICE_NAME, '--no-pager'])
    print()
    run(['journalctl', '-u', SERVICE_NAME, '-n', '20', '--no-pager'])
    print()
    run(['systemctl', 'status', KEEPALIVE_SERVICE_NAME, '--no-pager'])
    print()
    cfg = load_config()
    dev = cfg.get('DEV')
    print(f"{MENU}Configured TAP device:{NC} {dev if dev else 'None'}")
    if not dev:
        pause()
        return
    try:
        with open(f'/sys/class/net/{dev}/operstate') as f: raw_state = f.read().strip().lower()
    except: raw_state = 'unknown'
    state = 'UP' if raw_state in ('up','unknown') else 'DOWN'
    try:
        with open(f'/sys/class/net/{dev}/mtu') as f: mtu = f.read().strip()
    except: mtu = 'unknown'
    try:
        ip_output = subprocess.check_output(['ip','-4','addr','show','dev',dev], text=True)
        m = re.search(r'inet\s+([\d\.]+)/', ip_output)
        ipv4 = m.group(1) if m else 'None'
    except:
        ipv4 = 'None'
    print("\033[93m" + "─"*39 + "\033[0m")
    print(f"{OPTION}TAP Interface Info:{NC}")
    print(f"  Device: {dev}")
    print(f"  State : {state}")
    print(f"  MTU   : {mtu}")
    print(f"  IPv4  : {ipv4}/{cfg['LOCAL'].split('/',1)[1] if cfg['LOCAL'] else ''}")
    print("\033[93m" + "─"*39 + "\033[0m")
    pause()

def main():
    root()
    while True:
        os.system("clear")
        logo()
        print("\033[92m ^ ^\033[0m")
        print("\033[92m(\033[91mO,O\033[92m)\033[0m")
        print("\033[92m(   ) \033[93mLayer-2 TAP Tunnel \033[92mMain Menu\033[0m")
        print('\033[92m "-"\033[93m' + "═"*50 + '\033[0m')
        print("1)\033[93m Install Layer2-Tap\033[0m")
        print("2)\033[92m Configure Server\033[0m")
        print("3)\033[94m Configure Client\033[0m")
        print("4)\033[92m Edit Tunnel\033[0m")
        print("5)\033[91m Uninstall\033[0m")
        print("6)\033[93m Status & Logs\033[0m")
        print("7)\033[94m Reset Timer\033[0m")
        print("q)\033[97m Quit\033[0m")
        print('\033[93m' + "╰" + "─"*39 + '╯\033[0m')
        choice = input("\033[97mChoose an option [1-7, q]:\033[0m ")
        if choice == '1':
            install_stuff()
        elif choice == '2':
            install_server()
        elif choice == '3':
            install_client()
        elif choice == '4':
            edit_stuff()
        elif choice == '5':
            uninstall()
        elif choice == '6':
            status()
        elif choice == '7':
            reset_timer()
        elif choice.lower() == 'q':
            sys.exit(0)
        else:
            print(f"{ERROR}✖ Wrong option.{NC}")
            time.sleep(1)

main()
