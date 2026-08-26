import os
import time
import subprocess
import requests

from config import TOR_PORTS, TOR_DIRS, TOR_START_DELAY
from utils import Color


def start_tor():
    print(f"{Color.GREEN}[*] Starting 5 Tor instances...{Color.RESET}")
    try:
        subprocess.run(["killall", "tor"], capture_output=True)
    except FileNotFoundError:
        pass
    time.sleep(1)

    for i, (port, dirpath) in enumerate(zip(TOR_PORTS, TOR_DIRS)):
        os.makedirs(dirpath, exist_ok=True)
        subprocess.Popen(
            ["tor", "--RunAsDaemon", "1", "--SocksPort", str(port),
             "--DataDirectory", dirpath, "--Log", f"notice file {dirpath}/tor.log"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"{Color.GRAY}  [*] Tor instance {i+1} started on port {port}{Color.RESET}")

    print(f"{Color.GREEN}[*] Waiting for Tor circuits to establish...{Color.RESET}")
    time.sleep(TOR_START_DELAY)


def check_tor():
    print(f"{Color.GREEN}[*] Checking Tor connections...{Color.RESET}")
    working = []
    failed = list(TOR_PORTS)

    max_retries = 3
    for retry in range(1, max_retries + 1):
        still_failed = []
        for port in failed:
            try:
                r = requests.get(
                    "https://check.torproject.org/api/ip",
                    proxies={"http": f"socks5h://localhost:{port}",
                             "https": f"socks5h://localhost:{port}"},
                    timeout=10
                )
                data = r.json()
                ip = data.get("IP", "?")
                print(f"{Color.GREEN}  [+] Tor on port {port}: OK (IP: {ip}){Color.RESET}")
                working.append(port)
            except Exception:
                print(f"{Color.RED}  [!] Tor on port {port}: FAILED{Color.RESET}")
                still_failed.append(port)

        failed = still_failed
        if not failed:
            break

        if retry < max_retries:
            print(f"{Color.YELLOW}[*] Retry {retry}/{max_retries} for {len(failed)} failed instance(s) in 5s...{Color.RESET}")
            time.sleep(5)

    print(f"\n{Color.GREEN}[*] Working Tor instances: {len(working)}/5{Color.RESET}")

    if len(working) < 3:
        print(f"{Color.RED}[!] Need at least 3 Tor instances to run. Only {len(working)} working.{Color.RESET}")
        print(f"{Color.RED}[!] Check your Tor configuration and try again.{Color.RESET}")
        return []

    if len(working) < 5:
        print(f"{Color.YELLOW}[!] Warning: Running with {len(working)} threads instead of 5{Color.RESET}")

    return working


def rotate_tor():
    print(f"{Color.GREEN}[*] Rotating Tor circuits...{Color.RESET}")
    try:
        subprocess.run(["killall", "-HUP", "tor"], capture_output=True)
    except FileNotFoundError:
        pass
    time.sleep(3)
